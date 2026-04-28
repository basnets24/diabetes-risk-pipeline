# Imports
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler
from pyspark.sql.functions import col, when


# Step 1: Create Spark session
spark=SparkSession.builder.appName("DiabetesFeatureEngineering").getOrCreate()

# Step 2: Load data from Google Cloud Storage
INPUT_PATH="gs://team10-diabetes-data/processed/final_df"
df=spark.read.parquet(INPUT_PATH)

# Step 3: Create Comorbidity Flag (New Binary Column)
# If a patient has both hypertension and heart disease, we will flag them as having comorbidity 1, otherwise 0
df_with_flag=df.withColumn("comorbidity",
                           when((col("hypertension")==1) & (col("heart_disease")==1), 1).otherwise(0)
                           )

# Step 4: Encode Categorical Columns (Text -> Numbers -> One-Hot Vectors)
categorical_cols=["age_bucket", "bmi_category"]

# Creating StringIndexer (text -> numeric index)
indexers=[
    StringIndexer(
    inputCol=c,
    outputCol=f"{c}_index",
    handleInvalid="keep"
)
    for c in categorical_cols
]

# Creating OneHotEncoders (index -> binary vector)
encoders=[
    OneHotEncoder(
        inputCol=f"{c}_index",
        outputCol=f"{c}_ohe",
        handleInvalid="keep"
    )
    for c in categorical_cols
]

# Step 5: Vector Assembler (Combine All features into ONE Vector column)
feature_columns=[
    "age_bucket_ohe",       # One-hot encoded
    "bmi_category_ohe",     # One-hot encoded
    "hypertension",         # Original binary
    "heart_disease",        # Original binary
    "comorbidity",          # New binary flag
    "bmi"                   # Original numeric column
]
assembler=VectorAssembler(
    inputCols=feature_columns, # List of columns to combine
    outputCol="features",       # Name of combined vector column
    handleInvalid="keep"
)

# Step 6: Create a Pipeline
pipeline=Pipeline(
    stages=indexers+encoders+[assembler]    # Combine all lists into big list
)

# Fit the pipeline on data and transform
feature_table=pipeline.fit(df_with_flag).transform(df_with_flag)

# Step 7: Log Feature Dimension
sample_vector=feature_table.select("features").first()[0]
print(f"Feature Vector Dimension: {sample_vector.size}")

# Step 8: Save the feature table back to Google Cloud Storage
OUTPUT_PATH_feature_table="gs://team10-diabetes-data/features/feature_table"
final_to_save=feature_table.select("features", "diabetes")
final_to_save.write.mode("overwrite").parquet(OUTPUT_PATH_feature_table)

# Step 9: Stop Spark Session
spark.stop()