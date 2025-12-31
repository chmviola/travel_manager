pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = "travel_manager"
        DJANGO_ENV = "production"
    }

    stages {
        // REMOVIDA A ETAPA DE CHECKOUT MANUAL
        // O Jenkins já fez o checkout automaticamente ao iniciar o job.
        
        stage('Validar Arquivos') {
            steps {
                script {
                    // Vamos listar os arquivos só para garantir que tudo está lá
                    sh 'ls -la'
                    echo 'Verificando se o docker-compose.yml existe...'
                    sh 'ls -la docker-compose.yml'
                }
            }
        }

        stage('Deploy via Portainer') {
            steps {
                script {
                    echo 'Solicitando atualização ao Portainer...'
                    
                    // Substitua pela URL que você copiou no Passo 3
                    // O comando curl faz uma requisição POST que aciona o Portainer
                    sh 'curl -X POST -d "" "https://portainer.chmviola.com.br/api/stacks/webhooks/e36b671e-703c-4e51-a4b7-07ab0f0ca7a7"'
                    
                    echo 'Sinal enviado! O Portainer vai baixar o código e recriar a stack.'
                }
            }
        }

        stage('Health Check') {
            steps {
                script {
                    echo 'Aguardando containers subirem...'
                    sleep 15
                    // Verifica se o container web está rodando
                    sh 'docker ps | grep travel_manager_web'
                }
            }
        }
    }

    post {
        success {
            echo 'Sucesso! O ambiente PRODUCTION foi atualizado.'
        }
        failure {
            echo 'FALHA no deploy da branch main.'
        }
    }
}