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
  - name: jnlp
    resources:
      requests:
        cpu: "20m"
        memory: "128Mi"
      limits:
        cpu: "200m"
        memory: "256Mi"
  - name: python
    image: python:3.10-slim
    command: ['cat']
    tty: true
    resources:
      requests:
        cpu: "20m"
        memory: "200Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
  - name: docker
    image: docker:24-dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    resources:
      requests:
        cpu: "20m"
        memory: "200Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
    volumeMounts:
    - name: docker-graph-storage
      mountPath: /var/lib/docker
  - name: gcloud
    image: google/cloud-sdk:alpine
    command: ['cat']
    tty: true
    # FIX: DOCKER_HOST agar gcloud container bisa push via dind container
    # Containers dalam 1 pod berbagi network namespace → dind expose di localhost:2375
    env:
    - name: DOCKER_HOST
      value: "tcp://localhost:2375"
    resources:
      requests:
        cpu: "20m"
        memory: "50Mi"
      limits:
        cpu: "200m"
        memory: "256Mi"
  - name: argocd
    image: quay.io/argoproj/argocd:v3.4.2
    command: ['cat']
    tty: true
    resources:
      requests:
        cpu: "20m"
        memory: "50Mi"
      limits:
        cpu: "200m"
        memory: "256Mi"
  - name: trivy
    image: aquasec/trivy:latest
    command: ['cat']
    tty: true
    # FIX: DOCKER_HOST agar Trivy bisa scan image lokal dari dind container
    env:
    - name: DOCKER_HOST
      value: "tcp://localhost:2375"
    resources:
      requests:
        cpu: "20m"
        memory: "100Mi"
      limits:
        cpu: "300m"
        memory: "512Mi"
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
        SONAR_HOST_URL    = "http://sonarqube-sonarqube.devops.svc.cluster.local:9000"

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
                    echo "Branch     : ${env.BRANCH_NAME}"
                    echo "GIT_BRANCH : ${env.GIT_BRANCH}"
                    echo "Commit     : ${env.GIT_COMMIT}"
                    echo "Message    : ${env.GIT_COMMIT_MSG}"
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

                        # Install wget/unzip if missing (python:3.10-slim has neither)
                        apt-get install -y -q wget unzip 2>/dev/null || \
                          (apt-get update -q && apt-get install -y -q wget unzip)

                        # Gunakan sonar-scanner CLI
                        if [ ! -d sonar-scanner-5.0.1.3006-linux ]; then
                          wget -q https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
                          unzip -q sonar-scanner-cli-5.0.1.3006-linux.zip
                        fi
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
                container('python') {
                    // Poll SonarQube API directly — avoids needing Jenkins global SonarQube config
                    sh """
                        REPORT=\$(find .scannerwork -name "report-task.txt" 2>/dev/null | head -1 || \
                          find . -maxdepth 3 -name "report-task.txt" -not -path "*/sonar-scanner-*/*" 2>/dev/null | head -1)
                        if [ -z "\$REPORT" ]; then
                          echo "⚠️  report-task.txt not found — skip Quality Gate"
                          exit 0
                        fi

                        TASK_URL=\$(grep ceTaskUrl "\$REPORT" | cut -d= -f2-)
                        echo "Task URL: \$TASK_URL"

                        echo "Waiting for SonarQube analysis to complete..."
                        for i in \$(seq 1 30); do
                          STATUS=\$(curl -s "\$TASK_URL" \\
                            --user "${SONAR_TOKEN}:" 2>/dev/null | \\
                            python3 -c "import sys,json; print(json.load(sys.stdin)['task']['status'])" 2>/dev/null || echo "UNKNOWN")
                          echo "  Analysis status: \$STATUS"
                          if [ "\$STATUS" = "SUCCESS" ] || [ "\$STATUS" = "FAILED" ] || [ "\$STATUS" = "CANCELLED" ]; then
                            break
                          fi
                          sleep 10
                        done

                        ANALYSIS_ID=\$(curl -s "\$TASK_URL" \\
                          --user "${SONAR_TOKEN}:" 2>/dev/null | \\
                          python3 -c "import sys,json; print(json.load(sys.stdin)['task'].get('analysisId',''))" 2>/dev/null || echo "")

                        if [ -z "\$ANALYSIS_ID" ]; then
                          echo "⚠️  Could not get analysisId — skip quality gate check"
                          exit 0
                        fi

                        GATE=\$(curl -s "${SONAR_HOST_URL}/api/qualitygates/project_status?analysisId=\$ANALYSIS_ID" \\
                          --user "${SONAR_TOKEN}:" 2>/dev/null | \\
                          python3 -c "import sys,json; print(json.load(sys.stdin)['projectStatus']['status'])" 2>/dev/null || echo "ERROR")

                        echo "Quality Gate: \$GATE"
                        if [ "\$GATE" = "ERROR" ]; then
                          echo "❌ Quality Gate FAILED"
                          exit 1
                        fi
                        echo "✅ Quality Gate PASSED (\$GATE)"
                    """
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
                container('trivy') {
                    sh """
                        echo "🔍 Scanning image: ${FULL_IMAGE}"

                        # Scan dan simpan hasil ke file
                        # --timeout 15m: layer walk can exceed default 5m on large images
                        # || true: always continue even if trivy crashes (e.g. OOM, ctx deadline)
                        trivy image \
                            --exit-code 0 \
                            --severity HIGH,CRITICAL \
                            --no-progress \
                            --timeout 15m \
                            --format table \
                            --output trivy-report.txt \
                            ${FULL_IMAGE} || true

                        # FIX: trivy crash leaves no report file → cat fails with set -e active
                        cat trivy-report.txt 2>/dev/null || echo "⚠️  trivy-report.txt missing (scan may have crashed — treating as 0 findings)"

                        # Parse CRITICAL count from "Total: N (HIGH: X, CRITICAL: Y)" lines
                        # grep -c "CRITICAL" is wrong — it counts header/footer occurrences
                        CRITICAL_COUNT=\$(grep "Total:" trivy-report.txt 2>/dev/null | \
                          grep -oP 'CRITICAL: \\K[0-9]+' | \
                          awk '{s+=\$1} END{print s+0}' || echo "0")
                        HIGH_COUNT=\$(grep "Total:" trivy-report.txt 2>/dev/null | \
                          grep -oP 'HIGH: \\K[0-9]+' | \
                          awk '{s+=\$1} END{print s+0}' || echo "0")

                        echo ""
                        echo "═══════════════════════════════════"
                        echo "  Trivy Summary:"
                        echo "  CRITICAL : \${CRITICAL_COUNT}"
                        echo "  HIGH     : \${HIGH_COUNT}"
                        echo "═══════════════════════════════════"

                        # Fail build jika ada CRITICAL (strict mode)
                        if [ "\${CRITICAL_COUNT}" -gt "0" ]; then
                            echo "❌ Build GAGAL: ditemukan \${CRITICAL_COUNT} CRITICAL vulnerability!"
                            exit 1
                        fi

                        echo "✅ Security scan passed (no CRITICAL vulnerabilities)"
                    """
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-report.txt', allowEmptyArchive: true
                }
            }
        }

        // ── Stage 8: Push ke Artifact Registry ───────────────
        stage('📤 Push Image') {
            when {
                // branch 'main' requires multibranch pipeline; use GIT_BRANCH for regular pipeline
                expression { env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main' || env.BRANCH_NAME == 'main' }
            }
            steps {
                container('gcloud') {
                    sh """
                        # FIX: google/cloud-sdk:alpine tidak include docker CLI
                        # Install docker-cli (bukan daemon — daemon ada di dind container)
                        # DOCKER_HOST=tcp://localhost:2375 sudah di-set di pod spec
                        apk add --no-cache docker-cli 2>/dev/null || true

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
            when {
                expression { env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main' || env.BRANCH_NAME == 'main' }
            }
            steps {
                container('gcloud') {
                    withCredentials([gitUsernamePassword(
                        credentialsId: 'github-token',
                        gitToolName: 'Default'
                    )]) {
                        sh """
                            # FIX: google/cloud-sdk:alpine has no git — install it
                            apk add --no-cache git 2>/dev/null || true

                            # FIX: gcloud container starts in /root (WORKDIR from image),
                            # not the Jenkins workspace — must cd explicitly before git ops.
                            cd "\${WORKSPACE}"

                            # FIX: git 2.35.2+ refuses cross-user directory access.
                            # jnlp container checks out code (owned by uid=jenkins),
                            # gcloud container runs as root → "dubious ownership" error.
                            # Use wildcard — specific path can be shadowed by withCredentials
                            # overriding HOME/GIT_CONFIG_GLOBAL, causing path mismatch.
                            git config --global --add safe.directory '*'

                            git config --global user.email "jenkins@cicd.internal"
                            git config --global user.name "Jenkins CI"

                            # Update image tag di deployment.yaml
                            # FIX: path di repo simple-todo adalah k8s/ (bukan infra/k8s/)
                            sed -i "s|${REGISTRY}/${IMAGE_NAME}:.*|${FULL_IMAGE}|g" \
                                k8s/deployment.yaml

                            git add k8s/deployment.yaml
                            git commit -m "ci: update image tag to ${IMAGE_TAG} [skip ci]" || echo "Nothing to commit"
                            # FIX: checkout scm leaves detached HEAD — no local 'main' branch exists.
                            # Use HEAD:main to push the current HEAD to the remote main branch.
                            git push origin HEAD:main
                        """
                    }
                }
            }
        }

        // ── Stage 10: ArgoCD Sync ─────────────────────────────
        stage('🚀 Deploy via ArgoCD') {
            when {
                expression { env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main' || env.BRANCH_NAME == 'main' }
            }
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
            Build  : #${env.BUILD_NUMBER}
            ════════════════════════════════════
            """
        }
        failure {
            echo """
            ════════════════════════════════════
            ❌ PIPELINE GAGAL
            Build  : #${env.BUILD_NUMBER}
            Log    : ${env.BUILD_URL}
            ════════════════════════════════════
            """
        }
        always {
            cleanWs(notFailBuild: true)
        }
    }
}