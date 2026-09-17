pipeline {
    agent any

    environment {
        IMAGE_NAME = "naim8855/flask-app:latest"
        NETWORK_NAME = "myapp-network"
        VOLUME_NAME = "db-data"
    }

    stages {

        stage('Pull Flask Image') {
            steps {
                sh 'docker pull $IMAGE_NAME'
            }
        }

        stage('Ensure Network Exists') {
            steps {
                sh '''
                    docker network inspect $NETWORK_NAME >/dev/null 2>&1 || \
                    docker network create $NETWORK_NAME
                '''
            }
        }

        stage('Ensure Volume Exists') {
            steps {
                sh '''
                    docker volume inspect $VOLUME_NAME >/dev/null 2>&1 || \
                    docker volume create $VOLUME_NAME
                '''
            }
        }

        stage('Start Database') {
            steps {
                sh '''
                    docker rm -f db-container || true
                    docker run -d \
                      --name db-container \
                      --network $NETWORK_NAME \
                      -e MYSQL_ROOT_PASSWORD=rootpass \
                      -e MYSQL_DATABASE=mydb \
                      -e MYSQL_USER=flaskuser \
                      -e MYSQL_PASSWORD=flaskpass \
                      -v $VOLUME_NAME:/var/lib/mysql \
                      mysql:8
                '''
            }
        }

        stage('Wait for Database') {
            steps {
                sh '''
                    for i in $(seq 1 20); do
                        docker exec db-container mysqladmin ping -uroot -prootpass --silent && break
                        echo "Waiting for MySQL..."
                        sleep 3
                    done
                '''
            }
        }

        stage('Deploy Flask App') {
            steps {
                sh '''
                    docker rm -f flask-container || true
                    docker run -d \
                      --name flask-container \
                      --network $NETWORK_NAME \
                      -p 5000:5000 \
                      $IMAGE_NAME
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    sleep 5
                    curl -f http://localhost:5000
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully — app is running on port 5000.'
        }
        failure {
            echo 'Pipeline failed — check the stage logs above.'
        }
    }
}
