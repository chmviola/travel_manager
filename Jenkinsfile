pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = "travel_manager"
        DJANGO_ENV = "production"
        
        // Sua imagem no DockerHub
        DOCKER_IMAGE = "chmviola/travelmanager" 
        
        // ID da credencial de Login do DockerHub (Username/Password)
        DOCKER_CREDS_ID = "dockerhub_travel_manager"
    }

    stages {
        stage('Validar Arquivos') {
            steps {
                script {
                    sh 'ls -la'
                    echo 'Verificando se o docker-compose.yml existe...'
                    sh 'ls -la docker-compose.yml'
                }
            }
        }

        stage('Build da Imagem') {
            steps {
                script {
                    echo "Iniciando build da imagem: ${DOCKER_IMAGE}:${BUILD_NUMBER}"
                    // Constrói a imagem usando a pasta ./app como contexto
                    // Cria duas tags: :latest (para o Portainer usar) e :vX (para histórico)
                    sh "docker build -t ${DOCKER_IMAGE}:latest -t ${DOCKER_IMAGE}:${BUILD_NUMBER} ./app"
                }
            }
        }

        stage('Push para DockerHub') {
            steps {
                script {
                    echo 'Fazendo login e enviando para o DockerHub...'
                    // Usa as credenciais cadastradas no Jenkins para logar com segurança
                    withCredentials([usernamePassword(credentialsId: DOCKER_CREDS_ID, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh "echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin"
                        sh "docker push ${DOCKER_IMAGE}:latest"
                        sh "docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}"
                    }
                }
            }
        }

        stage('Limpeza Local') {
            steps {
                script {
                    echo 'Removendo imagens locais para economizar espaço no Jenkins...'
                    // Remove apenas do servidor Jenkins, pois já estão salvas no Hub
                    sh "docker rmi ${DOCKER_IMAGE}:${BUILD_NUMBER}"
                    sh "docker rmi ${DOCKER_IMAGE}:latest"
                }
            }
        }

        stage('Deploy via Portainer') {
            steps {
                // Busca a URL do Webhook nas credenciais secretas 
                withCredentials([string(credentialsId: 'portainer-webhook-prod', variable: 'WEBHOOK_URL')]) {
                    script {
                        echo 'Solicitando atualização ao Portainer...'
                        // O Portainer receberá o sinal, baixará a tag :latest do Hub e recriará o container
                        sh 'curl -X POST -d "" "$WEBHOOK_URL"'
                        echo 'Sinal enviado com sucesso.'
                    }
                }
            }
        }

        stage('Health Check') {
            steps {
                script {
                    echo 'Aguardando Portainer realizar o deploy...'
                    // Aumentei o tempo pois baixar do DockerHub leva alguns segundos a mais que o build local
                    sleep 30 
                    sh 'docker ps | grep travel_manager_web'
                }
            }
        }
    }

    post {
        success {
            echo "Sucesso! Build ${BUILD_NUMBER} enviado para DockerHub e deploy acionado."
        }
        failure {
            echo 'FALHA no pipeline.'
        }
    }
}