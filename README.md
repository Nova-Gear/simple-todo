# Simple Todo CI/CD & Kubernetes Deployment

Proyek ini mendemonstrasikan implementasi full-cycle DevOps mulai dari CI/CD (Jenkins, SonarQube) hingga Orchestration (Kubernetes) dengan fitur Autoscaling.

## 🚀 Fitur Utama
- **CI/CD Pipeline**: Otomatisasi Build, Test (Pytest), dan Analisis Kode (SonarQube).
- **Containerization**: Dockerization aplikasi Flask dengan Python 3.10.
- **Orchestration**: Deployment ke Kubernetes dengan Horizontal Pod Autoscaler (HPA).
- **Autoscaling**: Spawning pod otomatis (2 hingga 10 pods) berdasarkan beban CPU.

---

## 🛠 Persiapan Infrastruktur

### 1. Menjalankan Stack CI/CD
Gunakan Docker Compose untuk menjalankan Jenkins, SonarQube, dan Database.

```bash
# Copy environment file
cp .env.example .env

# Jalankan infrastruktur
docker-compose up -d
```

| Service | URL | Keterangan |
|---|---|---|
| Jenkins | `http://localhost:8080` | Alat otomatisasi CI/CD |
| SonarQube | `http://localhost:9000` | Analisis kualitas kode |
| **App (Production - K8s)** | **`http://localhost:30001`** | **Jalur utama dengan fitur Autoscaling & Pods** |
| App (Dev - Docker) | `http://localhost:5001` | Hanya untuk cek build lokal (Tanpa Autoscaling) |

> **PENTING**: Fitur **Horizontal Pod Autoscaler (HPA)** dan penambahan Pods secara otomatis hanya aktif jika Anda mengakses/mengetes melalui jalur **Kubernetes (Port 30001)**.

---

## 🏗 Konfigurasi Jenkins & SonarQube

### SonarQube
1. Login ke SonarQube (`admin/admin`).
2. Buat project baru: `simple-todo`.
3. Generate token dan simpan di Jenkins Credentials.

### Jenkins
1. Install plugin: `SonarQube Scanner` & `Docker Pipeline`.
2. Tambahkan Credentials:
   - `sonar-token`: Secret text (Token dari SonarQube).
3. Buat Pipeline Job dan hubungkan ke repository ini.

---

## ☸️ Kubernetes Deployment

### 1. Build Image Lokal
Pastikan image sudah tersedia di Docker lokal sebelum deploy ke K8s.
```bash
docker build -t nova-gear/simple-todo:latest ./repo-temp
```

### 2. Deploy ke Cluster
```bash
# Masuk ke folder k8s atau jalankan dari root
kubectl apply -f k8s/
```

### 3. Aktifkan Metrics Server (Penting untuk HPA)
Agar HPA bisa membaca penggunaan CPU, Metrics Server harus aktif:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

---

## 📈 Load Testing & Autoscaling

Untuk menguji apakah Kubernetes benar-benar menambah pod saat trafik tinggi:

1. **Pantau HPA di terminal 1:**
   ```bash
   kubectl get hpa todo-hpa -w
   ```

2. **Jalankan Load Test di terminal 2:**
   ```bash
   chmod +x load-test.sh
   ./load-test.sh
   ```

3. **Observasi**:
   - Ketika CPU usage melewati **50%**, Kubernetes akan mengubah replika dari 2 menjadi lebih banyak (maksimal 10).
   - Cek jumlah pods: `kubectl get pods`.

---

## 📁 Struktur Folder
- `app/`: Source code Flask API.
- `static/`: Frontend (HTML/JS/CSS).
- `k8s/`: Manifest Kubernetes (Deployment, Service, HPA).
- `tests/`: Unit testing dengan Pytest.
- `Jenkinsfile`: Definisi pipeline Jenkins.
- `load-test.sh`: Skrip simulasi trafik tinggi.

---
Dikembangkan oleh **Nova-Gear** untuk keperluan testing CI/CD & Kubernetes.
