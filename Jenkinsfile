pipeline {
    agent any

    environment {
        SONAR_SCANNER_HOME = tool 'SonarScanner'
        DOCKER_IMAGE = "nova-gear/simple-todo"
        REPO_URL = 'https://github.com/Nova-Gear/simple-todo.git'
    }

    stages {

        stage('Environment Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            environment {
                // Memanggil ID yang kita buat di Jenkins UI tadi
                DB_SECRET = credentials('mysql-mac-local')
                DB_NAME   = credentials('mysql-db-name') // Secret Text berisi nama DB
            }

            steps {
                sh '''
                    export DB_HOST=host.docker.internal
                    export DB_PORT=3306
                    export DB_USERNAME=${DB_SECRET_USR}
                    export DB_PASSWORD=${DB_SECRET_PSW}
                    export DB_DATABASE=${DB_NAME}
                    # pytest tests/ || echo "Tests failed but continuing for demo"
                    . venv/bin/activate
    pytest tests/
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh "${SONAR_SCANNER_HOME}/bin/sonar-scanner"
                }
            }
        }
        stage('Docker Build') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:${env.BUILD_NUMBER} ."
                sh "docker tag ${DOCKER_IMAGE}:${env.BUILD_NUMBER} ${DOCKER_IMAGE}:latest"
            }

            // Opsional: Push ke Docker Hub jika diperlukan agar ArgoCD bisa menarik image-nya
            /*
            withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
                sh "docker push ${DOCKER_IMAGE}:${env.BUILD_NUMBER}"
            }
            */
        }

        stage('Update Manifest') {
            steps {
                // Menggunakan Credentials Jenkins untuk Push ke Git
                // ID 'github-creds' harus berisi Personal Access Token (PAT) GitHub Anda
                withCredentials([usernamePassword(credentialsId: 'github-creds', passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
                    sh """
                        # Konfigurasi identitas Git
                        git config user.email "jenkins@ci.com"
                        git config user.name "Jenkins Automation"

                        # Update tag image di deployment.yaml menggunakan sed
                        # Mencari baris image: nova-gear/simple-todo:... dan menggantinya dengan tag baru
                        sed -i 's|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${env.BUILD_NUMBER}|g' k8s/deployment.yaml

                        # Commit perubahan
                        git add k8s/deployment.yaml
                        git commit -m "chore: update image tag to build ${env.BUILD_NUMBER} [skip ci]"

                        # Push kembali ke repository
                        # Menggunakan format https://username:token@github.com/...
                        git push https://${GIT_USERNAME}:${GIT_PASSWORD}@${REPO_URL} HEAD:main
                    """
                }
            }
        }

        // --- Model GitOps dengan ArgoCD ---
        // Dalam model GitOps sejati, Jenkins akan mengupdate tag image di file manifest Git.
        // Untuk lab ini, ArgoCD akan memantau folder k8s/ dan melakukan sync otomatis.
        stage('Wait for ArgoCD Sync') {
            steps {
                echo "Jenkins selesai melakukan CI. Sekarang ArgoCD akan melakukan deployment otomatis berdasarkan manifest di Git."
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Please check the logs.'
        }
    }
}
