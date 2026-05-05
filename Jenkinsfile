pipeline {
    agent any

    environment {
        SONAR_SCANNER_HOME = tool 'SonarScanner'
        DOCKER_IMAGE = "nova-gear/simple-todo"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/Nova-Gear/simple-todo.git'
            }
        }

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
                    # Jalankan MySQL sementara untuk testing jika diperlukan
                    # Namun untuk efisiensi di Jenkins, kita bisa menggunakan mock atau DB lokal
                    # Di sini kita asumsikan tests/ sudah menangani koneksi atau di-skip jika gagal
                    . venv/bin/activate
                    export DB_HOST=localhost
                    export DB_PORT=3306
                    export DB_USERNAME=root
                    export DB_PASSWORD=test
                    export DB_DATABASE=test_db
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

        // stage('Docker Push') {
        //     steps {
        //         withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
        //             sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
        //             sh "docker push ${DOCKER_IMAGE}:${env.BUILD_NUMBER}"
        //             sh "docker push ${DOCKER_IMAGE}:latest"
        //         }
        //     }
        // }
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
