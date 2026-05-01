# Imports
from pyspark.sql import SparkSession
from pyspark.ml.classification import LogisticRegression
from pyspark.sql.functions import col

# Step 1: Create Spark Session
spark=SparkSession.builder.appName("DiabetesLogisticRegression").getOrCreate()

# Step 2: Load data from Google Cloud Storage
INPUT_PATH="gs://team10-diabetes-data/features/feature_table"
df=spark.read.parquet(INPUT_PATH)

# step 3: Train/Test split (80/20 with fixed seed)
train_df, test_df=df.randomSplit([0.8, 0.2], seed=42)

# Log row counts
train_count=train_df.count()
test_count=test_df.count()
print(f"Training set count: {train_count}")
print(f"Test set count: {test_count}")

# Step 4: Initialize and fit Logistic Regression model
lr=LogisticRegression(featuresCol="features", labelCol="diabetes", predictionCol="prediction")
lr_model=lr.fit(train_df)

# Step 5: Output predictions and Probabilities
predictions=lr_model.transform(test_df)

# Show sample predictions
predictions.select("features", "diabetes", "probability", "prediction").show(10)

# Step 6: Save the model to Google Cloud Storage
MODEL_PATH="gs://team10-diabetes-data/models/logistic_regression"
lr_model.write().overwrite().save(MODEL_PATH)
print(f"SUCCESS: Model saved to {MODEL_PATH}")

# Step 6.5: Save the predictions data to GCS
PREDICTIONS_PATH="gs://team10-diabetes-data/predictions/logistic_regression"
predictions.write.mode("overwrite").parquet(PREDICTIONS_PATH)
print(f"SUCCESS: Predictions saved to {PREDICTIONS_PATH}")

# Step 7: Stop Spark
spark.stop()