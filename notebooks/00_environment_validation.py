# Databricks notebook source
print("F1 Lakehouse - Environment Validation")
print(f"Spark version: {spark.version}")

# COMMAND ----------

data = [
    (1, "Norris", 25),
    (2, "Verstappen", 18),
    (3, "Russell", 15)
]

columns = ["position", "driver", "points"]

df = spark.createDataFrame(data, columns)

display(df)

# COMMAND ----------

spark.sql("SHOW CATALOGS").show()

spark.sql("SHOW SCHEMAS IN f1_lakehouse").show()

# COMMAND ----------

storage_account = "stf1lakehouse290"

for layer in ["bronze", "silver", "gold"]:
    path = (
        f"abfss://{layer}@"
        f"{storage_account}.dfs.core.windows.net/"
    )

    print(f"Testing {layer.upper()}")

    files = dbutils.fs.ls(path)

    print(f"Connection successful: {len(files)} items")