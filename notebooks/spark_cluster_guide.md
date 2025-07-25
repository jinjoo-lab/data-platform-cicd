# 🐳 Docker Compose Spark 클러스터 사용 가이드

## 📋 클러스터 구성

- **Spark Master**: `localhost:7077` (Web UI: `http://localhost:8080`)
- **Spark Worker 1**: Web UI at `http://localhost:8081`
- **Spark Worker 2**: Web UI at `http://localhost:8082`

## 🚀 시작하기

### 1. Spark 클러스터 시작
```bash
docker-compose up -d
```

### 2. 클러스터 상태 확인
```bash
docker-compose ps
```

### 3. Spark Master Web UI 접속
브라우저에서 `http://localhost:8080` 접속

### 4. Jupyter 노트북 실행
```bash
# 로컬에서 Jupyter 실행
jupyter lab
```

## 📊 데이터 분석

### Jupyter에서 클러스터 연결
`notebooks/pyspark_setup.ipynb`에서:
- `USE_CLUSTER = True` 설정
- 자동으로 Docker Compose Spark 클러스터에 연결

### 클러스터 vs 로컬 모드 전환
```python
USE_CLUSTER = True   # 클러스터 모드
USE_CLUSTER = False  # 로컬 모드
```

## 🔧 클러스터 관리

### 로그 확인
```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs spark-master
docker-compose logs spark-worker-1
```

### 클러스터 중지
```bash
docker-compose down
```

### 리소스 정리
```bash
docker-compose down -v  # 볼륨까지 삭제
```

## 💡 팁

1. **메모리 설정**: `docker-compose.yaml`에서 `SPARK_WORKER_MEMORY` 조정
2. **CPU 코어**: `SPARK_WORKER_CORES` 조정  
3. **데이터 접근**: `/opt/bitnami/spark/data`에 마운트된 데이터 사용
4. **스케일링**: `docker-compose up --scale spark-worker=3` 으로 워커 수 증가

## 🌐 유용한 URL

- Spark Master UI: http://localhost:8080
- Worker 1 UI: http://localhost:8081  
- Worker 2 UI: http://localhost:8082
- Jupyter Lab: http://localhost:8888 (로컬 실행시) 