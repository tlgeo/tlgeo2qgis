pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Unit Tests') {
            steps {
                echo 'Running Unit Tests with mocked QGIS environment...'
                sh 'chmod +x scripts/run_tests.sh'
                sh './scripts/run_tests.sh'
            }
        }

        stage('Integration Tests') {
            parallel {
                stage('QGIS 3 (3.28 LTR)') {
                    steps {
                        echo 'Running Integration Tests on QGIS 3...'
                        sh 'chmod +x scripts/run_integration_tests.sh'
                        sh './scripts/run_integration_tests.sh release-3_28'
                    }
                }
                stage('QGIS 4 (Latest)') {
                    steps {
                        echo 'Running Integration Tests on QGIS 4...'
                        sh 'chmod +x scripts/run_integration_tests.sh'
                        sh './scripts/run_integration_tests.sh latest'
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
