pipeline {
    agent {
        docker { 
            image 'python:3.10-slim' 
            // Baris ini memastikan Jenkins bisa menjalankan perintah docker di dalam stage Docker Build nanti
            args '-u root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        SONAR_SCANNER_HOME = tool 'SonarScanner'
        DOCKER_IMAGE = "nova-gear/simple-todo"
    }

    stages {
        // stage('Checkout') {
        //     steps {
        //         git branch: 'main', credentialsId: 'github-creds', url: 'https://github.com/Nova-Gear/simple-todo.git'
        //     }
        // }

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
            steps {
                sh '''
                    # Jalankan MySQL sementara untuk testing jika diperlukan.
                    # Karena kita sudah punya layanan 'todo-db' di docker-compose,
                    # Jenkins bisa mengaksesnya menggunakan hostname 'todo-db' 
                    # jika Jenkins berjalan di network yang sama.
                    . venv/bin/activate
                    export DB_HOST=todo-db
                    export DB_PORT=3306
                    export DB_USERNAME=${MYSQL_USER:-todo_user}
                    export DB_PASSWORD=${MYSQL_PASSWORD:-todo_password}
                    export DB_DATABASE=${MYSQL_DATABASE:-todo_app}
                    # pytest tests/ || echo "Tests failed but continuing for demo"
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

        //     steps {
        //         withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
        //             sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
        //             sh "docker push ${DOCKER_IMAGE}:${env.BUILD_NUMBER}"
        //             sh "docker push ${DOCKER_IMAGE}:latest"
        //         }
        //     }
        // }
        // }

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
