# Databricks notebook source
# MAGIC %md
# MAGIC # Single table column transformation

# COMMAND ----------

bronze = "abfss://bronze@intechfirstsg.dfs.core.windows.net"
silver = "abfss://silver@intechfirstsg.dfs.core.windows.net"

# COMMAND ----------

dbutils.fs.ls(f"{bronze}/SalesLT/")

# COMMAND ----------

dbutils.fs.ls(f"{silver}/")

# COMMAND ----------

df = spark.read.format("parquet").load(f"{bronze}/SalesLT/Address/Address.parquet")

# COMMAND ----------

display(df)

# COMMAND ----------

from pyspark.sql.functions import from_utc_timestamp, date_format
from pyspark.sql.types import TimestampType

df = df.withColumn("ModifiedDate", date_format(from_utc_timestamp(df['ModifiedDate'].cast(TimestampType()), "UTC"), "yyyy-mm-dd"))

# COMMAND ----------

display(df)

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT 1 AS column1

# COMMAND ----------

# MAGIC %md
# MAGIC # Date transformation for tables

# COMMAND ----------

table_name = []

for i in dbutils.fs.ls(f"{bronze}/SalesLT/"):
    table_name.append(i.name.split('/')[0])

table_name

# COMMAND ----------

from pyspark.sql.functions import from_utc_timestamp, date_format
from pyspark.sql.types import TimestampType

for i in table_name:
    path = f"{bronze}/SalesLT/{i}/{i}.parquet"
    df = spark.read.format("parquet").load(path)
    column = df.columns

    for col in column:
        if "Date" in col or "date" in col:
            df = df.withColumn(col, date_format(from_utc_timestamp(df[col].cast(TimestampType()), "UTC"), "yyyy-MM-dd"))

    output_path = f"{silver}/SalesLT/{i}/"
    df.write.format("delta").mode("overwrite").save(output_path)

# COMMAND ----------

display(df)