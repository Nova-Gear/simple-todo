// ═══════════════════════════════════════════════════════════
//  Jenkinsfile — simple-todo (Flask Python + MySQL)
//  Pipeline: Checkout → Pytest → SonarQube → Docker Build → Push → ArgoCD
// ═══════════════════════════════════════════════════════════

pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: agent
spec:
  serviceAccountName: jenkins-sa
  containers:
  - name: python
    image: python:3.10-slim
    command: ['cat']
    tty: true
    resources:
      requests:
        cpu: "500m"
        memory: "512Mi"
      limits:
        cpu: "1"
        memory: "1Gi"
  - name: docker
    image: docker:24-dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    volumeMounts:
    - name: docker-graph-storage
      mountPath: /var/lib/docker
  - name: gcloud
    image: google/cloud-sdk:alpine
    command: ['cat']
    tty: true
  - name: argocd
    image: argoproj/argocd:v2.9.0
    command: ['cat']
    tty: true
  volumes:
  - name: docker-graph-storage
    emptyDir: {}
"""
        }
    }

    environment {
        PROJECT_ID    = "project-741337ff-4507-4f1d-8f6"
        REGION        = "asia-southeast2"
        REGISTRY      = "${REGION}-docker.pkg.dev/${PROJECT_ID}/todo-repo"
        IMAGE_NAME    = "simple-todo"
        IMAGE_TAG     = "${env.BUILD_NUMBER}-${env.GIT_COMMIT?.take(7) ?: 'latest'}"
        FULL_IMAGE    = "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

        SONAR_PROJECT_KEY = "Simple-Todo"
        SONAR_HOST_URL    = "http://sonarqube.devops.svc.cluster.local:9000"

        ARGOCD_SERVER  = "argocd-server.argocd.svc.cluster.local"
        ARGOCD_APP     = "simple-todo"

        SONAR_TOKEN  = credentials('sonar-token')
        ARGOCD_TOKEN = credentials('argocd-auth-token')
    }

    options {
        timeout(time: 45, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    stages {
        // ── Stage 1: Checkout ────────────────────────────────
        stage('📥 Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_MSG = sh(
                        script: 'git log -1 --pretty=%B',
                        returnStdout: true
                    ).trim()
                    echo "Branch : ${env.BRANCH_NAME}"
                    echo "Commit : ${env.GIT_COMMIT}"
                    echo "Message: ${env.GIT_COMMIT_MSG}"
                }
            }
        }

        // ── Stage 2: Setup Virtualenv & Install deps ─────────
        stage('📦 Install Dependencies') {
            steps {
                container('python') {
                    sh '''
                        python --version
                        pip --version

                        # Buat virtualenv
                        python -m venv .venv
                        . .venv/bin/activate

                        # Install dependencies
                        pip install --upgrade pip
                        pip install -r requirements.txt

                        echo "Dependencies installed:"
                        pip list
                    '''
                }
            }
        }

        // ── Stage 3: Unit Tests (Pytest) ─────────────────────
        stage('🧪 Run Tests') {
            steps {
                container('python') {
                    sh '''
                        . .venv/bin/activate
                        pip install pytest-cov

                        pytest tests/ \
                            --cov=app \
                            --cov-report=xml:coverage.xml \
                            --cov-report=term-missing \
                            --junitxml=test-results.xml \
                            -v
                    '''
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }

        // ── Stage 4: SonarQube Analysis ──────────────────────
        stage('🔍 SonarQube Analysis') {
            steps {
                container('python') {
                    sh '''
                        . .venv/bin/activate
                        pip install sonar-scanner-cli 2>/dev/null || true

                        # Gunakan sonar-scanner langsung
                        wget -q https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
                        unzip -q sonar-scanner-cli-5.0.1.3006-linux.zip
                        export PATH="$PWD/sonar-scanner-5.0.1.3006-linux/bin:$PATH"

                        sonar-scanner \
                            -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                            -Dsonar.projectName="Simple Todo" \
                            -Dsonar.projectVersion=${IMAGE_TAG} \
                            -Dsonar.sources=app \
                            -Dsonar.tests=tests \
                            -Dsonar.language=py \
                            -Dsonar.python.version=3.10 \
                            -Dsonar.python.coverage.reportPaths=coverage.xml \
                            -Dsonar.host.url=${SONAR_HOST_URL} \
                            -Dsonar.login=${SONAR_TOKEN} \
                            -Dsonar.sourceEncoding=UTF-8
                    '''
                }
            }
        }

        // ── Stage 5: Quality Gate ─────────────────────────────
        stage('🚦 Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        // ── Stage 6: Docker Build ─────────────────────────────
        stage('🐳 Docker Build') {
            steps {
                container('docker') {
                    sh """
                        docker build \
                            --build-arg BUILD_DATE=\$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
                            --build-arg GIT_COMMIT=${env.GIT_COMMIT} \
                            --build-arg VERSION=${IMAGE_TAG} \
                            --tag ${FULL_IMAGE} \
                            --tag ${REGISTRY}/${IMAGE_NAME}:latest \
                            --file Dockerfile \
                            .

                        echo "Image built: ${FULL_IMAGE}"
                        docker images | grep ${IMAGE_NAME}
                    """
                }
            }
        }

        // ── Stage 7: Security Scan (Trivy) ───────────────────
        stage('🔒 Security Scan') {
            steps {
                container('docker') {
                    sh """
                        # Download trivy
                        wget -qO- https://github.com/aquasecurity/trivy/releases/download/v0.49.1/trivy_0.49.1_Linux-64bit.tar.gz | tar xz trivy

                        ./trivy image \
                            --exit-code 0 \
                            --severity HIGH,CRITICAL \
                            --no-progress \
                            --format table \
                            ${FULL_IMAGE}
                    """
                }
            }
        }

        // ── Stage 8: Push ke Artifact Registry ───────────────
        stage('📤 Push Image') {
            when {
                branch 'main'
            }
            steps {
                container('gcloud') {
                    sh """
                        gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
                        docker push ${FULL_IMAGE}
                        docker push ${REGISTRY}/${IMAGE_NAME}:latest
                        echo "✅ Pushed: ${FULL_IMAGE}"
                    """
                }
            }
        }

        // ── Stage 9: Update image tag di manifest ────────────
        stage('📝 Update Manifest') {
            when { branch 'main' }
            steps {
                container('gcloud') {
                    withCredentials([gitUsernamePassword(
                        credentialsId: 'github-token',
                        gitToolName: 'Default'
                    )]) {
                        sh """
                            git config user.email "jenkins@cicd.internal"
                            git config user.name "Jenkins CI"

                            # Update image tag di deployment.yaml
                            sed -i "s|${REGISTRY}/${IMAGE_NAME}:.*|${FULL_IMAGE}|g" \
                                infra/k8s/deployment.yaml

                            git add infra/k8s/deployment.yaml
                            git commit -m "ci: update image tag to ${IMAGE_TAG} [skip ci]" || echo "Nothing to commit"
                            git push origin main
                        """
                    }
                }
            }
        }

        // ── Stage 10: ArgoCD Sync ─────────────────────────────
        stage('🚀 Deploy via ArgoCD') {
            when { branch 'main' }
            steps {
                container('argocd') {
                    sh """
                        argocd login ${ARGOCD_SERVER} \
                            --auth-token ${ARGOCD_TOKEN} \
                            --insecure \
                            --grpc-web

                        argocd app sync ${ARGOCD_APP} --timeout 120 --prune
                        argocd app wait ${ARGOCD_APP} --health --timeout 300

                        echo "✅ Deploy berhasil: ${ARGOCD_APP} @ ${IMAGE_TAG}"
                    """
                }
            }
        }
    }

    post {
        success {
            echo """
            ════════════════════════════════════
            ✅ PIPELINE BERHASIL
            Image  : ${FULL_IMAGE}
            Branch : ${env.BRANCH_NAME}
            Build  : #${BUILD_NUMBER}
            ════════════════════════════════════
            """
        }
        failure {
            echo """
            ════════════════════════════════════
            ❌ PIPELINE GAGAL
            Build  : #${BUILD_NUMBER}
            Log    : ${BUILD_URL}
            ════════════════════════════════════
            """
        }
        always {
            cleanWs()
        }
    }
}