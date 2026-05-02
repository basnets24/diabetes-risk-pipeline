from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, count, mean, lit

spark = SparkSession.builder \
    .appName("RiskAggregation") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

df = spark.read.parquet("gs://team10-diabetes-data/predictions/v2_final_dataset") \
    .select("row_id", "diabetes", "lr_prob_calibrated",
            "hbA1c_level", "blood_glucose_level", "bmi", "age", "hypertension", "heart_disease") \
    .withColumnRenamed("lr_prob_calibrated", "prob_diabetic")

def agg(bucketed_df, bucket_col, dimension_label):
    return bucketed_df.groupBy(bucket_col).agg(
        count("*").alias("n"),
        mean("prob_diabetic").alias("avg_prob"),
        mean("diabetes").alias("diabetic_rate"),
    ).withColumnRenamed(bucket_col, "bucket") \
     .withColumn("dimension", lit(dimension_label)) \
     .select("dimension", "bucket", "n", "avg_prob", "diabetic_rate")

hba1c = agg(
    df.withColumn("hba1c_bin",
        when(col("hbA1c_level") < 5.7,  "Normal (<5.7)")
        .when(col("hbA1c_level") < 6.5, "Prediabetes (5.7-6.4)")
        .otherwise("Diabetic (>=6.5)")),
    "hba1c_bin", "hbA1c_level"
)

glucose = agg(
    df.withColumn("glucose_bin",
        when(col("blood_glucose_level") < 100, "Normal (<100)")
        .when(col("blood_glucose_level") < 126, "Prediabetes (100-125)")
        .otherwise("High (>=126)")),
    "glucose_bin", "blood_glucose_level"
)

bmi = agg(
    df.withColumn("bmi_bin",
        when(col("bmi") < 18.5, "Underweight (<18.5)")
        .when(col("bmi") < 25,  "Normal (18.5-24.9)")
        .when(col("bmi") < 30,  "Overweight (25-29.9)")
        .otherwise("Obese (>=30)")),
    "bmi_bin", "bmi"
)

age = agg(
    df.withColumn("age_bin",
        when(col("age") < 18, "Children (<18)")
        .when(col("age") < 35, "Young (18-34)")
        .when(col("age") < 55, "Middle (35-54)")
        .otherwise("Senior (>=55)")),
    "age_bin", "age"
)

hyp = agg(
    df.withColumn("hyp_bin", col("hypertension").cast("string")),
    "hyp_bin", "hypertension"
)

hd = agg(
    df.withColumn("hd_bin", col("heart_disease").cast("string")),
    "hd_bin", "heart_disease"
)

result = hba1c.union(glucose).union(bmi).union(age).union(hyp).union(hd)

result.coalesce(1).write.mode("overwrite").option("header", "true").csv(
    "gs://team10-diabetes-data/evaluation/risk_aggregation_lr"
)

print("Risk aggregation saved")
spark.stop()
