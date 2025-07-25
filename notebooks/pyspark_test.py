#!/usr/bin/env python3
"""
🐳 PySpark 클러스터 테스트 스크립트

Docker Compose Spark 클러스터와 연동하여 ITWorld 뉴스 데이터를 분석합니다.
Jupyter Lab 노트북이 문제가 있을 때 대안으로 사용하세요.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from datetime import datetime

def create_spark_session(use_cluster=True):
    """Spark 세션을 생성합니다."""
    
    # Docker Compose Spark 클러스터 연결 설정
    SPARK_MASTER_URL = "spark://localhost:7077"
    
    if use_cluster:
        print(f"🐳 Docker Compose Spark 클러스터에 연결 중...")
        print(f"Master URL: {SPARK_MASTER_URL}")
        
        # 클러스터 모드로 Spark 세션 생성
        spark = SparkSession.builder \
            .appName("ITWorld News Analysis - Cluster") \
            .master(SPARK_MASTER_URL) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "1g") \
            .config("spark.executor.cores", "2") \
            .getOrCreate()
    else:
        print(f"💻 로컬 Spark 모드로 실행 중...")
        
        # 로컬 모드로 Spark 세션 생성
        spark = SparkSession.builder \
            .appName("ITWorld News Analysis - Local") \
            .master("local[*]") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()

    print(f"\n🚀 Spark 세션이 시작되었습니다!")
    print(f"Spark 버전: {spark.version}")
    print(f"Spark UI: {spark.sparkContext.uiWebUrl}")
    print(f"실행 모드: {'🐳 클러스터' if use_cluster else '💻 로컬'}")
    
    return spark

def load_itworld_data(spark):
    """ITWorld 뉴스 데이터를 로드합니다."""
    
    data_base_path = "../data"
    
    try:
        itworld_dirs = [d for d in os.listdir(data_base_path) if d.startswith("ITWorld_")]
        
        if itworld_dirs:
            latest_dir = sorted(itworld_dirs)[-1]
            data_path = os.path.join(data_base_path, latest_dir)
            print(f"📁 데이터 디렉터리: {data_path}")
            
            # JSON 파일 찾기
            json_files = [f for f in os.listdir(data_path) if f.endswith('.json')]
            
            if json_files:
                json_file = os.path.join(data_path, json_files[0])
                print(f"📄 JSON 파일: {json_file}")
                
                # Spark DataFrame으로 로드
                df = spark.read.option("multiline", "true").json(json_file)
                
                print(f"\n📊 데이터 로드 완료!")
                print(f"총 {df.count()}개의 뉴스 기사")
                print(f"\n📋 데이터 스키마:")
                df.printSchema()
                
                return df
                
            else:
                print("❌ JSON 파일을 찾을 수 없습니다.")
                return None
                
        else:
            print("❌ ITWorld 데이터 디렉터리를 찾을 수 없습니다.")
            print("💡 먼저 다음 명령으로 데이터를 수집해주세요:")
            print("   cd collectors/crawler && python news_main.py --main-page -f")
            return None
            
    except Exception as e:
        print(f"❌ 데이터 로드 중 오류 발생: {e}")
        print("💡 data 디렉터리가 존재하는지 확인해주세요.")
        return None

def analyze_data(df):
    """기본 데이터 분석을 수행합니다."""
    
    if df is None:
        print("⚠️ 데이터가 없어서 분석을 수행할 수 없습니다.")
        return
    
    print("\n" + "="*50)
    print("📈 기본 데이터 분석 시작")
    print("="*50)
    
    # 1. 데이터 샘플 보기
    print("\n📋 데이터 샘플 (상위 5개):")
    df.select("title", "description", "category", "published_date").show(5, truncate=False)
    
    # 2. 카테고리별 뉴스 수
    print("\n🏷️ 카테고리별 뉴스 수:")
    category_counts = df.groupBy("category").count().orderBy(desc("count"))
    category_counts.show()
    
    # 3. 텍스트 길이 통계
    print("\n📊 텍스트 길이 통계:")
    df_with_stats = df.withColumn("title_length", length(col("title"))) \
                      .withColumn("desc_length", length(col("description")))
    
    df_with_stats.select("title_length", "desc_length").describe().show()
    
    # 4. 키워드 분석
    print("\n🔍 제목에서 자주 등장하는 키워드:")
    words_df = df.select(explode(split(col("title"), "\\s+")).alias("word")) \
                  .filter(length(col("word")) >= 3) \
                  .groupBy("word") \
                  .count() \
                  .orderBy(desc("count"))
    
    print("상위 10개 키워드:")
    words_df.show(10, truncate=False)
    
    return category_counts, df_with_stats

def main():
    """메인 함수"""
    
    print("🐳 PySpark 클러스터 테스트 시작!")
    print("=" * 60)
    
    # 🚀 1. Spark 세션 생성
    USE_CLUSTER = True  # False로 변경하면 로컬 모드
    spark = create_spark_session(USE_CLUSTER)
    
    # 📁 2. 데이터 로드
    df = load_itworld_data(spark)
    
    # 📈 3. 데이터 분석
    if df is not None:
        analyze_data(df)
    
    # 🛑 4. 세션 종료 안내
    print("\n" + "="*60)
    print("🎉 분석 완료!")
    print("\n📌 다음 단계:")
    print("1. 🐳 클러스터 모니터링: http://localhost:8080")
    print("2. 📊 코드를 수정해서 추가 분석을 진행하세요")
    print("3. 🔄 spark.stop()으로 세션을 종료하세요")
    print("\n💡 Jupyter Lab이 작동하면 pyspark_setup.ipynb를 사용하세요!")
    
    return spark, df

if __name__ == "__main__":
    spark, df = main() 