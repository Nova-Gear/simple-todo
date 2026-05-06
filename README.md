# Simple Todo — Full-Cycle CI/CD & Kubernetes Deployment

Proyek ini mendemonstrasikan implementasi **full-cycle DevOps** pada aplikasi Flask (Python 3.10) dengan MySQL, mulai dari CI/CD Pipeline (Jenkins + SonarQube) hingga Orchestration & Autoscaling (Kubernetes + ArgoCD).

---

## 📋 Daftar Isi

1. [Arsitektur & Alur Kerja](#-arsitektur--alur-kerja)
2. [Prasyarat](#-prasyarat)
3. [Struktur Proyek](#-struktur-proyek)
4. [Quick Start — Menjalankan Stack](#-quick-start--menjalankan-stack)
5. [Setup Jenkins (Detail)](#-setup-jenkins-detail)
6. [Setup SonarQube (Detail)](#-setup-sonarqube-detail)
7. [Integrasi Jenkins ↔ SonarQube](#-integrasi-jenkins--sonarqube)
8. [Konfigurasi Pipeline Jenkins](#-konfigurasi-pipeline-jenkins)
9. [Setup Kubernetes (Detail)](#️-setup-kubernetes-detail)
10. [GitOps dengan ArgoCD](#-gitops-dengan-argocd)
11. [Load Testing & Autoscaling](#-load-testing--autoscaling)
12. [Troubleshooting](#-troubleshooting)

---

## 🏗 Arsitektur & Alur Kerja

```
Developer ─── Git Push ───▶ GitHub Repository
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                             ▼
               Jenkins (CI)                  ArgoCD (CD)
            ┌──────────────┐           ┌──────────────────┐
            │ 1. Checkout  │           │ Monitor folder   │
            │ 2. Venv+Deps │           │ k8s/ di GitHub   │
            │ 3. Pytest    │           │ Auto-sync ke K8s │
            │ 4. SonarScan │           └──────────────────┘
            │ 5. Docker    │                    │
            │    Build     │                    ▼
            └──────────────┘           ┌──────────────────┐
                                       │   Kubernetes     │
                                       │  ┌────────────┐  │
                                       │  │ Pod 1      │  │
                                       │  │ Pod 2      │  │
                                       │  │ ...Pod N   │  │
                                       │  │ (HPA: 2-10)│  │
                                       │  └────────────┘  │
                                       └──────────────────┘
```

**Alur singkat:**
1. Developer push kode ke GitHub.
2. Jenkins otomatis menjalankan: **Test → SonarQube Analysis → Docker Build**.
3. ArgoCD memantau folder `k8s/` dan men-deploy perubahan manifest ke Kubernetes secara otomatis.
4. HPA (Horizontal Pod Autoscaler) menambah/mengurangi pod berdasarkan beban CPU.

---

## ✅ Prasyarat

Pastikan tools berikut sudah terinstal di mesin Anda:

| Tool | Versi Minimum | Cara Cek | Fungsi |
|------|---------------|----------|--------|
| **Docker** | 20.x | `docker --version` | Container runtime |
| **Docker Compose** | 2.x | `docker compose version` | Orchestrasi container lokal |
| **kubectl** | 1.25+ | `kubectl version --client` | CLI Kubernetes |
| **Kubernetes Cluster** | 1.25+ | `kubectl cluster-info` | Minikube / Docker Desktop K8s |
| **Git** | 2.x | `git --version` | Version control |

### Mengaktifkan Kubernetes di Docker Desktop

Jika Anda menggunakan **Docker Desktop** (macOS/Windows):

1. Buka **Docker Desktop** → **Settings** (ikon gear).
2. Navigasi ke tab **Kubernetes**.
3. Centang **Enable Kubernetes**.
4. Klik **Apply & Restart** — tunggu hingga indikator Kubernetes berwarna hijau.
5. Verifikasi:
   ```bash
   kubectl cluster-info
   # Output: Kubernetes control plane is running at https://127.0.0.1:6443
   ```

### Menggunakan Minikube (Alternatif)

```bash
# Install minikube (macOS)
brew install minikube

# Start cluster
minikube start --driver=docker --cpus=4 --memory=4096

# Verifikasi
kubectl cluster-info
```

---

## 📁 Struktur Proyek

```
simple-todo/
├── app/                          # Source code Flask API
│   ├── __init__.py
│   ├── app.py                    # Factory create_app()
│   ├── config.py                 # Konfigurasi dari environment
│   ├── database.py               # Koneksi MySQL (PyMySQL)
│   ├── routes/                   # Endpoint API
│   └── services/                 # Business logic
├── static/                       # Frontend (HTML/JS/CSS)
├── tests/                        # Unit testing (Pytest)
│   ├── __init__.py
│   └── test_basic.py
├── k8s/                          # Manifest Kubernetes
│   ├── deployment.yaml           # Deployment app + MySQL
│   ├── service.yaml              # NodePort + ClusterIP service
│   ├── hpa.yaml                  # Horizontal Pod Autoscaler
│   └── argocd-app.yaml           # ArgoCD Application manifest
├── Dockerfile                    # Image untuk aplikasi Flask
├── Dockerfile.jenkins            # Custom Jenkins image + Docker CLI + Python
├── Jenkinsfile                   # Pipeline definition
├── docker-compose.yml            # Stack: Jenkins, SonarQube, PostgreSQL, MySQL, App
├── sonar-project.properties      # Konfigurasi SonarQube Scanner
├── load-test.sh                  # Script simulasi trafik tinggi
├── requirements.txt              # Python dependencies
├── run.py                        # Application entry point
├── .env.example                  # Template environment variables
└── .gitignore
```

---

## 🚀 Quick Start — Menjalankan Stack

### Step 1: Clone Repository

```bash
git clone https://github.com/Nova-Gear/simple-todo.git
cd simple-todo
```

### Step 2: Konfigurasi Environment

```bash
# Salin template environment
cp .env.example .env
```

Buka file `.env` dan sesuaikan jika diperlukan. Nilai default sudah siap pakai untuk development:

```env
# Jenkins
JENKINS_PORT=8080
JENKINS_AGENT_PORT=50000

# SonarQube
SONAR_PORT=9000

# PostgreSQL (database SonarQube)
POSTGRES_USER=sonar
POSTGRES_PASSWORD=sonar_password
POSTGRES_DB=sonarqube

# MySQL (database aplikasi Todo)
MYSQL_ROOT_PASSWORD=root_password
MYSQL_DATABASE=todo_app
MYSQL_USER=todo_user
MYSQL_PASSWORD=todo_password
```

### Step 3: Jalankan Seluruh Stack

```bash
docker-compose up -d
```

Tunggu semua container selesai start (~1-2 menit untuk SonarQube):

```bash
# Cek status container
docker-compose ps

# Output yang diharapkan — semua berstatus "Up"
# NAME           STATUS
# jenkins        Up
# sonarqube      Up
# sonarqube-db   Up (healthy)
# todo-db        Up (healthy)
# todo-app       Up
```

### Akses Dashboard

| Service | URL | Kredensial Default |
|---------|-----|--------------------|
| **Jenkins** | http://localhost:8080 | Lihat [Setup Jenkins](#-setup-jenkins-detail) |
| **SonarQube** | http://localhost:9000 | `admin` / `admin` |
| **Todo App (Docker)** | http://localhost:5001 | — |
| **Todo App (Kubernetes)** | http://localhost:30001 | — (aktif setelah K8s deploy) |

> **⚠️ PENTING**: Fitur **Horizontal Pod Autoscaler (HPA)** dan penambahan Pods otomatis hanya aktif melalui jalur **Kubernetes (Port 30001)**.

---

## 🔧 Setup Jenkins (Detail)

### Step 1: Ambil Initial Admin Password

Setelah `docker-compose up -d`, Jenkins memerlukan password awal untuk unlock:

```bash
# Tampilkan password dari container
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Salin output password tersebut.

### Step 2: Unlock Jenkins

1. Buka browser → **http://localhost:8080**.
2. Anda akan melihat halaman **"Unlock Jenkins"**.
3. Paste password dari step sebelumnya ke field **Administrator password**.
4. Klik **Continue**.

### Step 3: Install Plugins

1. Pilih **"Install suggested plugins"** — tunggu proses instalasi selesai.
2. Setelah selesai, Anda akan diminta membuat **Admin User**.

### Step 4: Buat Admin User

Isi form:
- **Username**: `admin` (atau sesuai preferensi)
- **Password**: password pilihan Anda
- **Full name**: nama Anda
- **E-mail**: email Anda

Klik **Save and Continue** → **Save and Finish** → **Start using Jenkins**.

### Step 5: Install Plugin Tambahan

Dari halaman utama Jenkins:

1. Navigasi ke **Manage Jenkins** → **Plugins** → tab **Available plugins**.
2. Cari dan install plugin berikut (centang lalu klik **Install**):

| Plugin | Fungsi |
|--------|--------|
| **SonarQube Scanner** | Integrasi analisis kode dengan SonarQube |
| **Docker Pipeline** | Build & push Docker image dari pipeline |
| **Pipeline** | Sudah termasuk di suggested plugins, pastikan aktif |

3. Setelah install, **restart Jenkins** jika diminta:
   ```bash
   docker restart jenkins
   ```

### Step 6: Konfigurasi Global Tool — SonarQube Scanner

1. Navigasi ke **Manage Jenkins** → **Tools**.
2. Scroll ke bagian **SonarQube Scanner installations**.
3. Klik **Add SonarQube Scanner**.
4. Isi:
   - **Name**: `SonarScanner` ← **harus persis seperti ini** (sesuai Jenkinsfile).
   - **Install automatically**: ✅ Centang.
   - **Version**: pilih versi terbaru yang tersedia.
5. Klik **Save**.

---

## 🔍 Setup SonarQube (Detail)

### Step 1: Login Pertama Kali

1. Buka browser → **http://localhost:9000**.
2. Tunggu hingga halaman selesai loading (SonarQube butuh ~1-2 menit untuk inisialisasi).
3. Login dengan kredensial default:
   - **Login**: `admin`
   - **Password**: `admin`
4. Anda akan diminta **mengganti password** — masukkan password baru dan simpan.

### Step 2: Buat Project Baru

1. Dari halaman utama, klik **"Create a local project"** (atau **Projects** → **Create Project**).
2. Isi:
   - **Project display name**: `Simple Todo`
   - **Project key**: `Simple-Todo` ← **harus persis seperti ini** (sesuai `sonar-project.properties`).
   - **Main branch name**: `main`
3. Klik **Next**.
4. Pilih **"Use the global setting"** untuk Quality Gate, lalu klik **Create project**.

### Step 3: Generate Authentication Token

1. Di halaman project yang baru dibuat, pilih **"Locally"** sebagai metode analisis.
2. Generate token:
   - **Token name**: `jenkins-token` (atau nama bebas).
   - **Type**: `Project Analysis Token`.
   - **Expires in**: `No expiration` (untuk lab/testing).
3. Klik **Generate**.
4. **⚠️ SALIN TOKEN SEKARANG** — token hanya ditampilkan sekali. Contoh format:
   ```
   sqp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
5. Simpan token ini untuk digunakan di konfigurasi Jenkins.

### Step 4: Verifikasi Konfigurasi

File `sonar-project.properties` di root project sudah dikonfigurasi:

```properties
sonar.projectKey=Simple-Todo
sonar.projectName=Simple Todo
sonar.projectVersion=1.0
sonar.sources=app
sonar.exclusions=static/**
sonar.python.version=3
sonar.language=py
sonar.sourceEncoding=UTF-8
sonar.host.url=http://sonarqube:9000
```

> **Catatan**: `sonar.host.url` menggunakan `http://sonarqube:9000` (hostname Docker) karena scanner dijalankan dari Jenkins yang berada di network Docker yang sama (`cicd-net`).

---

## 🔗 Integrasi Jenkins ↔ SonarQube

### Step 1: Simpan Token SonarQube di Jenkins

1. Di Jenkins, navigasi ke **Manage Jenkins** → **Credentials**.
2. Klik **System** → **Global credentials (unrestricted)**.
3. Klik **Add Credentials**.
4. Isi:
   - **Kind**: `Secret text`
   - **Scope**: `Global`
   - **Secret**: paste token SonarQube dari step sebelumnya (`sqp_xxx...`)
   - **ID**: `sonar-token`
   - **Description**: `SonarQube Authentication Token`
5. Klik **Create**.

### Step 2: Konfigurasi SonarQube Server di Jenkins

1. Navigasi ke **Manage Jenkins** → **System** (Configure System).
2. Scroll ke bagian **SonarQube servers**.
3. Centang **Environment variables**.
4. Klik **Add SonarQube**.
5. Isi:
   - **Name**: `SonarQube` ← **harus persis seperti ini** (sesuai Jenkinsfile: `withSonarQubeEnv('SonarQube')`).
   - **Server URL**: `http://sonarqube:9000` (hostname Docker internal).
   - **Server authentication token**: pilih credential `sonar-token` yang baru dibuat.
6. Klik **Save**.

---

## ⚙️ Konfigurasi Pipeline Jenkins

### Step 1: Buat Pipeline Job

1. Dari halaman utama Jenkins, klik **New Item**.
2. Isi:
   - **Enter an item name**: `simple-todo-pipeline`
   - Pilih **Pipeline**.
3. Klik **OK**.

### Step 2: Konfigurasi Source Code

Di halaman konfigurasi job:

1. Scroll ke bagian **Pipeline**.
2. Ubah **Definition** ke: **Pipeline script from SCM**.
3. Isi:
   - **SCM**: `Git`
   - **Repository URL**: `https://github.com/Nova-Gear/simple-todo.git`
   - **Credentials**: tambahkan GitHub credentials jika repository private (lihat Step 3).
   - **Branches to build**: `*/main`
   - **Script Path**: `Jenkinsfile` (default, biarkan).
4. Klik **Save**.

### Step 3: (Opsional) Tambah GitHub Credentials

Jika repository bersifat **private**:

1. Di bagian **Credentials**, klik **Add** → **Jenkins**.
2. Isi:
   - **Kind**: `Username with password`
   - **Username**: username GitHub Anda
   - **Password**: GitHub Personal Access Token (PAT)
   - **ID**: `github-creds`
3. Klik **Add**, lalu pilih credential yang baru dibuat.

### Step 4: (Opsional) Konfigurasi Webhook untuk Auto-Trigger

Agar pipeline berjalan otomatis setiap ada git push:

1. Di konfigurasi job, centang **GitHub hook trigger for GITScm polling** (bagian Build Triggers).
2. Di GitHub repository, navigasi ke **Settings** → **Webhooks** → **Add webhook**.
3. Isi:
   - **Payload URL**: `http://<IP-SERVER-ANDA>:8080/github-webhook/`
   - **Content type**: `application/json`
   - **Events**: pilih **Just the push event**.
4. Klik **Add webhook**.

> **Catatan**: Untuk development lokal, gunakan tool seperti [ngrok](https://ngrok.com/) untuk mengekspos Jenkins ke internet, atau jalankan pipeline secara manual.

### Step 5: Jalankan Pipeline

1. Kembali ke halaman job `simple-todo-pipeline`.
2. Klik **Build Now**.
3. Klik nomor build di **Build History** → **Console Output** untuk memantau progress.

### Penjelasan Stage Pipeline (Jenkinsfile)

```
┌──────────────────┐
│ Environment Setup│  → Buat virtualenv + install dependencies
└────────┬─────────┘
         ▼
┌──────────────────┐
│   Run Tests      │  → Jalankan pytest terhadap test suite
└────────┬─────────┘
         ▼
┌──────────────────┐
│ SonarQube        │  → Analisis kualitas kode & kirim ke SonarQube
│ Analysis         │
└────────┬─────────┘
         ▼
┌──────────────────┐
│  Docker Build    │  → Build image: nova-gear/simple-todo:<BUILD_NUMBER>
│                  │  → Tag sebagai :latest
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Wait for ArgoCD  │  → ArgoCD melakukan sync otomatis ke K8s
│ Sync             │
└──────────────────┘
```

---

## ☸️ Setup Kubernetes (Detail)

### Step 1: Pastikan Kubernetes Aktif

```bash
# Verifikasi cluster
kubectl cluster-info

# Cek nodes
kubectl get nodes
# Output: NAME             STATUS   ROLES           AGE   VERSION
#         docker-desktop   Ready    control-plane   ...   v1.xx.x
```

### Step 2: Install Metrics Server (Wajib untuk HPA)

Metrics Server diperlukan agar HPA bisa membaca penggunaan CPU/Memory:

```bash
# Install Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

**Untuk Docker Desktop / Minikube**, tambahkan flag `--kubelet-insecure-tls`:

```bash
# Patch Metrics Server agar bekerja di lingkungan lokal
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--kubelet-insecure-tls"
  }
]'
```

Verifikasi Metrics Server berjalan:

```bash
# Tunggu ~1 menit, lalu cek
kubectl top nodes
# Jika muncul data CPU/Memory, Metrics Server sudah aktif
```

### Step 3: Build Docker Image Lokal

Kubernetes memerlukan image Docker yang tersedia secara lokal:

```bash
# Build image aplikasi
docker build -t nova-gear/simple-todo:latest .
```

> **Catatan**: Di `deployment.yaml`, `imagePullPolicy` diset ke `Never` sehingga Kubernetes menggunakan image lokal dari Docker Desktop tanpa perlu push ke registry.

### Step 4: Deploy ke Kubernetes

```bash
# Apply semua manifest sekaligus
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

Atau sekaligus:

```bash
kubectl apply -f k8s/
```

> **Catatan**: Perintah ini juga akan meng-apply `argocd-app.yaml`. Jika ArgoCD belum terinstal, abaikan error untuk resource tersebut — deployment dan service tetap akan berjalan.

### Step 5: Verifikasi Deployment

```bash
# Cek pods (tunggu hingga STATUS = Running)
kubectl get pods
# Output yang diharapkan:
# NAME                        READY   STATUS    RESTARTS   AGE
# todo-app-xxxxxxxxx-xxxxx    1/1     Running   0          30s
# todo-app-xxxxxxxxx-xxxxx    1/1     Running   0          30s
# todo-db-xxxxxxxxx-xxxxx     1/1     Running   0          30s

# Cek services
kubectl get services
# Output:
# NAME              TYPE        CLUSTER-IP      PORT(S)          AGE
# todo-service      NodePort    10.x.x.x        80:30001/TCP     30s
# todo-db-service   ClusterIP   10.x.x.x        3306/TCP         30s

# Cek HPA
kubectl get hpa
# Output:
# NAME       REFERENCE             TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# todo-hpa   Deployment/todo-app   x%/50%    2         10        2          30s
```

### Step 6: Akses Aplikasi

Buka browser → **http://localhost:30001**

### Penjelasan Manifest Kubernetes

#### `deployment.yaml`

Berisi **2 Deployment**:

| Deployment | Image | Replicas | Deskripsi |
|-----------|-------|----------|-----------|
| `todo-app` | `nova-gear/simple-todo:latest` | 2 | Aplikasi Flask, CPU request 100m / limit 200m |
| `todo-db` | `mysql:8.0` | 1 | Database MySQL dengan emptyDir volume |

#### `service.yaml`

| Service | Type | Port | Deskripsi |
|---------|------|------|-----------|
| `todo-service` | NodePort | 80 → 5000, NodePort 30001 | Expose app ke luar cluster |
| `todo-db-service` | ClusterIP | 3306 | Internal, hanya bisa diakses dalam cluster |

#### `hpa.yaml`

| Parameter | Nilai | Deskripsi |
|-----------|-------|-----------|
| `minReplicas` | 2 | Minimum pod yang selalu berjalan |
| `maxReplicas` | 10 | Maksimum pod saat scaling |
| `targetCPUUtilization` | 50% | Threshold trigger scaling |

---

## 🚢 GitOps dengan ArgoCD

### Step 1: Install ArgoCD di Kubernetes

```bash
# Buat namespace khusus ArgoCD
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Tunggu semua pods ArgoCD ready (~2-3 menit)
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s
```

### Step 2: Akses Dashboard ArgoCD

```bash
# Port-forward ke localhost
kubectl port-forward svc/argocd-server -n argocd 8081:443
```

Buka browser → **https://localhost:8081** (terima warning SSL self-signed certificate).

### Step 3: Login ke ArgoCD

```bash
# Ambil password admin
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Login:
- **Username**: `admin`
- **Password**: output dari perintah di atas

### Step 4: Daftarkan Aplikasi

```bash
kubectl apply -f k8s/argocd-app.yaml
```

File `argocd-app.yaml` mengkonfigurasi:

```yaml
spec:
  source:
    repoURL: 'https://github.com/Nova-Gear/simple-todo.git'
    path: k8s                           # Monitor folder k8s/
  syncPolicy:
    automated:
      prune: true                       # Hapus resource yang tidak ada di Git
      selfHeal: true                    # Kembalikan state jika ada drift
```

Setelah terdaftar, ArgoCD akan **otomatis men-deploy** setiap perubahan yang di-push ke folder `k8s/` di repository.

### Step 5: Verifikasi di Dashboard

Buka dashboard ArgoCD → Anda akan melihat aplikasi `simple-todo-app` dengan status **Synced** dan **Healthy**.

---

## 📈 Load Testing & Autoscaling

Untuk membuktikan bahwa HPA bekerja dan Kubernetes menambah pod secara otomatis:

### Terminal 1 — Pantau HPA

```bash
# Watch mode: update real-time
kubectl get hpa todo-hpa -w
```

### Terminal 2 — Pantau Pods

```bash
# Watch mode: lihat pod baru muncul
kubectl get pods -w
```

### Terminal 3 — Jalankan Load Test

```bash
# Berikan izin eksekusi
chmod +x load-test.sh

# Jalankan (10 concurrent curl loops)
./load-test.sh
```

### Observasi yang Diharapkan

1. **Awal**: 2 pods berjalan, CPU usage rendah.
2. **~1-2 menit**: CPU usage naik melewati 50%, HPA mulai scaling.
3. **~3-5 menit**: Kubernetes menambah pods secara bertahap (hingga maksimal 10).
4. **Setelah stop load test** (`CTRL+C`): pods akan berkurang kembali ke 2 (~5-10 menit cooldown).

```
# Contoh output HPA saat scaling:
NAME       REFERENCE             TARGETS    MINPODS   MAXPODS   REPLICAS
todo-hpa   Deployment/todo-app   12%/50%    2         10        2
todo-hpa   Deployment/todo-app   68%/50%    2         10        2       ← Trigger!
todo-hpa   Deployment/todo-app   72%/50%    2         10        4       ← Scaled up!
todo-hpa   Deployment/todo-app   45%/50%    2         10        4       ← Stabil
```

---

## 🔥 Troubleshooting

### Jenkins tidak bisa build Docker image

**Gejala**: `permission denied` saat menjalankan `docker build` di pipeline.

**Solusi**: Pastikan Jenkins container memiliki akses ke Docker socket:
```bash
# Cek apakah volume mount sudah benar
docker inspect jenkins | grep -A5 "Binds"
# Harus ada: /var/run/docker.sock:/var/run/docker.sock
```

### SonarQube tidak bisa start / terus restart

**Gejala**: Container `sonarqube` keluar dengan error `vm.max_map_count`.

**Solusi** (Linux host):
```bash
sudo sysctl -w vm.max_map_count=262144
# Untuk persist setelah reboot:
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

### HPA menampilkan `<unknown>/50%`

**Gejala**: Metrics Server belum aktif atau belum ready.

**Solusi**:
```bash
# Cek apakah Metrics Server berjalan
kubectl get pods -n kube-system | grep metrics-server

# Jika ada tapi error, patch kubelet-insecure-tls
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
  {"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}
]'

# Tunggu ~1 menit, lalu cek lagi
kubectl get hpa todo-hpa
```

### Pod CrashLoopBackOff

**Gejala**: Pod terus restart.

**Solusi**:
```bash
# Cek log pod
kubectl logs <nama-pod>

# Cek events
kubectl describe pod <nama-pod>
```

Penyebab umum: database belum ready saat app start. Pastikan `todo-db` pod sudah **Running** sebelum `todo-app`.

### Tidak bisa akses localhost:30001

**Gejala**: Koneksi ditolak.

**Solusi**:
```bash
# Cek apakah service sudah ada
kubectl get svc todo-service

# Cek apakah ada pod yang Running
kubectl get pods -l app=todo

# Jika menggunakan Minikube:
minikube service todo-service --url
```

---

## 📝 Referensi Cepat — Perintah Penting

```bash
# === Docker Compose ===
docker-compose up -d              # Start semua service
docker-compose down               # Stop semua service
docker-compose logs -f jenkins    # Lihat log Jenkins
docker-compose logs -f sonarqube  # Lihat log SonarQube

# === Kubernetes ===
kubectl get all                   # Lihat semua resource
kubectl get pods -w               # Watch pods real-time
kubectl get hpa todo-hpa -w       # Watch HPA real-time
kubectl logs -f <pod-name>        # Tail log pod
kubectl delete -f k8s/            # Hapus semua resource K8s
kubectl apply -f k8s/             # Apply/update semua manifest

# === ArgoCD ===
kubectl port-forward svc/argocd-server -n argocd 8081:443
```

---

Dikembangkan oleh **Nova-Gear** untuk keperluan testing CI/CD & Kubernetes.
