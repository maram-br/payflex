pipeline {
    agent any

    parameters {
        choice(
            name: 'DEMO_SCENARIO',
            choices: ['success', 'performance_failure', 'secret_leak'],
            description: 'Scénario demandé pour les captures du TP'
        )
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    environment {
        LOCAL_IMAGE = "payflex:${BUILD_NUMBER}"
        GITLEAKS_IMAGE = 'zricethezav/gitleaks:v8.21.2'
        SONAR_IMAGE = 'sonarqube:10.6-community'
        SONAR_SCANNER_IMAGE = 'sonarsource/sonar-scanner-cli:5'
        CURL_IMAGE = 'curlimages/curl:8.10.1'
        NEWMAN_IMAGE = 'postman/newman:6.2.1'
        K6_IMAGE = 'grafana/k6:0.54.0'
        JENKINS_CONTAINER = 'payflex-jenkins'
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
            }
        }

        stage('1 - Confidentialité et construction') {
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail
                    mkdir -p source-content artifact-content reports
                    git ls-files -z | tar --null -T - -cf tracked-source.tar
                    tar -xf tracked-source.tar -C source-content
                    DEMO_SCENARIO_VALUE="${DEMO_SCENARIO:-success}"

                    if [ "$DEMO_SCENARIO_VALUE" = "secret_leak" ]; then
                        mkdir -p source-content/demo
                        printf 'demo_card=%s%s%s%s\n' '4111' '1111' '1111' '1111' > source-content/demo/pii.txt
                    fi

                    docker run --rm --user "$(id -u):$(id -g)" --volumes-from "$JENKINS_CONTAINER" \
                        "$GITLEAKS_IMAGE" detect --source "$PWD" --config="$PWD/.gitleaks.toml" \
                        --report-format json --report-path "$PWD/gitleaks-history.json" --exit-code 0

                    docker run --rm --user "$(id -u):$(id -g)" --volumes-from "$JENKINS_CONTAINER" \
                        "$GITLEAKS_IMAGE" detect --no-git --source "$PWD/source-content" \
                        --config="$PWD/.gitleaks.toml" --report-format json \
                        --report-path "$PWD/gitleaks-source.json" --exit-code 0

                    docker build -t "$LOCAL_IMAGE" .
                    docker create --name "payflex-extract-$BUILD_NUMBER" "$LOCAL_IMAGE"
                    docker cp "payflex-extract-$BUILD_NUMBER:/app" ./artifact-content/app
                    docker inspect "payflex-extract-$BUILD_NUMBER" > artifact-content/image-metadata.json
                    docker rm "payflex-extract-$BUILD_NUMBER"

                    # GPG_KEY est la clé publique de signature de l'image Python officielle.
                    # Toutes les autres variables et métadonnées restent analysées.
                    python3 - <<'PY'
import json
from pathlib import Path

path = Path("artifact-content/image-metadata.json")
metadata = json.loads(path.read_text(encoding="utf-8"))
for image in metadata:
    environment = image.get("Config", {}).get("Env", [])
    image["Config"]["Env"] = [
        item for item in environment if item.split("=", 1)[0] != "GPG_KEY"
    ]
path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
PY

                    docker run --rm --user "$(id -u):$(id -g)" --volumes-from "$JENKINS_CONTAINER" \
                        "$GITLEAKS_IMAGE" detect --no-git --source "$PWD/artifact-content" \
                        --config="$PWD/.gitleaks.toml" --report-format json \
                        --report-path "$PWD/gitleaks-artifacts.json" --exit-code 0

                    python3 scripts/quality_gate.py secrets \
                        gitleaks-history.json gitleaks-source.json gitleaks-artifacts.json
                '''
            }
            post {
                failure {
                    sh '''#!/bin/bash
                        mkdir -p reports
                        test -f reports/incident-secrets.md || printf '# Rapport d incident\n\n**Étape** : confidentialité / construction\n\n- Échec du scan ou de la construction Docker.\n' > reports/incident-build.md
                    '''
                }
                always {
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'gitleaks-*.json,reports/**'
                }
            }
        }

        stage('2 - Tests unitaires et couverture') {
            steps {
                sh '''#!/bin/bash
                    set -uo pipefail
                    mkdir -p logs reports
                    python3 -m venv .venv
                    .venv/bin/pip install -r requirements.txt

                    .venv/bin/python -m pytest --cov=app --cov-report=xml --cov-report=term \
                        --junitxml=reports/junit.xml 2>&1 | tee logs/pytest.log
                    TEST_STATUS=${PIPESTATUS[0]}

                    python3 scripts/quality_gate.py unit
                    COVERAGE_STATUS=$?

                    docker run --rm --user "$(id -u):$(id -g)" --volumes-from "$JENKINS_CONTAINER" \
                        "$GITLEAKS_IMAGE" detect --no-git --source "$PWD/logs" \
                        --config="$PWD/.gitleaks.toml" --report-format json \
                        --report-path "$PWD/gitleaks-unit-logs.json" --exit-code 0
                    python3 scripts/quality_gate.py secrets gitleaks-unit-logs.json
                    LOG_STATUS=$?

                    if [ "$TEST_STATUS" -ne 0 ]; then
                        printf '# Rapport d incident\n\n**Étape** : tests unitaires\n\n- Au moins un test PyTest a échoué.\n' > reports/incident-unit-tests.md
                    fi
                    exit $((TEST_STATUS || COVERAGE_STATUS || LOG_STATUS))
                '''
            }
            post {
                always {
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'coverage.xml,gitleaks-unit-logs.json,logs/**,reports/**'
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                }
            }
        }

        stage('3 - Analyse SonarQube') {
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail
                    CI_NETWORK="payflex-sonar-$BUILD_NUMBER"
                    SONAR_NAME="payflex-sonar-$BUILD_NUMBER"
                    docker network create "$CI_NETWORK"
                    docker run -d --name "$SONAR_NAME" --network "$CI_NETWORK" "$SONAR_IMAGE"

                    for i in $(seq 1 60); do
                        if docker run --rm --network "$CI_NETWORK" "$CURL_IMAGE" -s \
                            "http://$SONAR_NAME:9000/api/system/status" | grep -q '"status":"UP"'; then
                            break
                        fi
                        if [ "$i" -eq 60 ]; then
                            docker logs "$SONAR_NAME" | tail -50
                            exit 1
                        fi
                        sleep 5
                    done

                    NEW_PW="$(openssl rand -hex 12)Aa1!"
                    INIT_CRED="$(printf '%s:%s' admin admin)"
                    ADMIN_CRED="$(printf '%s:%s' admin "$NEW_PW")"
                    SONAR_URL="http://$SONAR_NAME:9000"

                    docker run --rm --network "$CI_NETWORK" "$CURL_IMAGE" -sf --user "$INIT_CRED" \
                        -X POST "$SONAR_URL/api/users/change_password" \
                        -d login=admin -d previousPassword=admin --data-urlencode "password=$NEW_PW"

                    TOKEN=$(docker run --rm --network "$CI_NETWORK" "$CURL_IMAGE" -sf --user "$ADMIN_CRED" \
                        -X POST "$SONAR_URL/api/user_tokens/generate" -d name=ci \
                        | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

                    sonar_post() {
                        docker run --rm --network "$CI_NETWORK" "$CURL_IMAGE" -sf --user "$ADMIN_CRED" -X POST "$@"
                    }
                    sonar_post "$SONAR_URL/api/qualitygates/create" -d name=PayFlex
                    sonar_post "$SONAR_URL/api/qualitygates/create_condition" -d gateName=PayFlex -d metric=coverage -d op=LT -d error=70
                    sonar_post "$SONAR_URL/api/qualitygates/create_condition" -d gateName=PayFlex -d metric=bugs -d op=GT -d error=0
                    sonar_post "$SONAR_URL/api/qualitygates/create_condition" -d gateName=PayFlex -d metric=vulnerabilities -d op=GT -d error=0
                    sonar_post "$SONAR_URL/api/qualitygates/set_as_default" -d name=PayFlex

                    docker run --rm --user "$(id -u):$(id -g)" --network "$CI_NETWORK" \
                        --volumes-from "$JENKINS_CONTAINER" -w "$PWD" \
                        -e SONAR_HOST_URL="$SONAR_URL" -e SONAR_TOKEN="$TOKEN" \
                        "$SONAR_SCANNER_IMAGE" \
                        -Dsonar.qualitygate.wait=true

                    TOKEN_CRED="$TOKEN:"
                    docker run --rm --network "$CI_NETWORK" "$CURL_IMAGE" -s --user "$TOKEN_CRED" \
                        "$SONAR_URL/api/measures/component?component=payflex&metricKeys=code_smells,coverage,sqale_index,bugs,vulnerabilities" \
                        > sonar-measures.json
                    python3 scripts/sonar_warnings.py
                '''
            }
            post {
                failure {
                    sh '''#!/bin/bash
                        mkdir -p reports
                        printf '# Rapport d incident\n\n**Étape** : SonarQube\n\n- Démarrage, analyse ou Quality Gate SonarQube en échec.\n' > reports/incident-sonar.md
                    '''
                }
                always {
                    sh '''#!/bin/bash
                        docker rm -f "payflex-sonar-$BUILD_NUMBER" >/dev/null 2>&1 || true
                        docker network rm "payflex-sonar-$BUILD_NUMBER" >/dev/null 2>&1 || true
                    '''
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'sonar-measures.json,reports/**'
                }
            }
        }

        stage('4 - Tests d intégration Newman') {
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail
                    CI_NETWORK="payflex-it-$BUILD_NUMBER"
                    APP_NAME="payflex-it-$BUILD_NUMBER"
                    mkdir -p logs reports
                    docker network create "$CI_NETWORK"
                    docker run -d --name "$APP_NAME" --network "$CI_NETWORK" "$LOCAL_IMAGE"

                    for i in $(seq 1 30); do
                        if docker run --rm --network "$CI_NETWORK" "$CURL_IMAGE" -sf "http://$APP_NAME:8000/health"; then
                            break
                        fi
                        if [ "$i" -eq 30 ]; then exit 1; fi
                        sleep 1
                    done

                    docker run --rm --user "$(id -u):$(id -g)" --network "$CI_NETWORK" \
                        --volumes-from "$JENKINS_CONTAINER" -w "$PWD" "$NEWMAN_IMAGE" run \
                        "$PWD/postman/payflex.postman_collection.json" \
                        --env-var "baseUrl=http://$APP_NAME:8000" \
                        --reporters cli,json --reporter-json-export "$PWD/reports/newman-report.json" \
                        2>&1 | tee logs/newman.log
                '''
            }
            post {
                failure {
                    sh '''#!/bin/bash
                        mkdir -p reports
                        printf '# Rapport d incident\n\n**Étape** : intégration\n\n- Démarrage API ou scénario Newman en échec.\n' > reports/incident-integration.md
                    '''
                }
                always {
                    sh '''#!/bin/bash
                        set +e
                        mkdir -p logs reports
                        docker logs "payflex-it-$BUILD_NUMBER" > logs/application-integration.log 2>&1
                        docker run --rm --user "$(id -u):$(id -g)" --volumes-from "$JENKINS_CONTAINER" \
                            "$GITLEAKS_IMAGE" detect --no-git --source "$PWD/logs" \
                            --config="$PWD/.gitleaks.toml" --report-format json \
                            --report-path "$PWD/gitleaks-integration-logs.json" --exit-code 0
                        python3 scripts/quality_gate.py secrets gitleaks-integration-logs.json
                        LOG_STATUS=$?
                        docker rm -f "payflex-it-$BUILD_NUMBER" >/dev/null 2>&1
                        docker network rm "payflex-it-$BUILD_NUMBER" >/dev/null 2>&1
                        exit "$LOG_STATUS"
                    '''
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'gitleaks-integration-logs.json,logs/**,reports/**'
                }
            }
        }

        stage('5 - Tests de performance k6') {
            steps {
                sh '''#!/bin/bash
                    set -uo pipefail
                    CI_NETWORK="payflex-perf-$BUILD_NUMBER"
                    APP_NAME="payflex-perf-$BUILD_NUMBER"
                    DEMO_SCENARIO_VALUE="${DEMO_SCENARIO:-success}"
                    DELAY_MS=0
                    if [ "$DEMO_SCENARIO_VALUE" = "performance_failure" ]; then DELAY_MS=600; fi

                    mkdir -p logs reports
                    docker network create "$CI_NETWORK"
                    docker run -d --name "$APP_NAME" --network "$CI_NETWORK" \
                        -e PAYFLEX_DELAY_MS="$DELAY_MS" "$LOCAL_IMAGE"

                    for i in $(seq 1 30); do
                        if docker run --rm --network "$CI_NETWORK" "$CURL_IMAGE" -sf "http://$APP_NAME:8000/health"; then
                            break
                        fi
                        if [ "$i" -eq 30 ]; then exit 1; fi
                        sleep 1
                    done

                    docker run --rm --user "$(id -u):$(id -g)" --network "$CI_NETWORK" \
                        --volumes-from "$JENKINS_CONTAINER" -w "$PWD" "$K6_IMAGE" run \
                        -e "BASE_URL=http://$APP_NAME:8000" "$PWD/perf/load.js" 2>&1 | tee logs/k6.log
                    K6_STATUS=${PIPESTATUS[0]}

                    python3 scripts/quality_gate.py perf
                    GATE_STATUS=$?
                    exit $((K6_STATUS || GATE_STATUS))
                '''
            }
            post {
                failure {
                    sh '''#!/bin/bash
                        mkdir -p reports
                        test -f reports/incident-perf.md || printf '# Rapport d incident\n\n**Étape** : performance\n\n- Tir k6 ou Quality Gate de performance en échec.\n' > reports/incident-performance.md
                    '''
                }
                always {
                    sh '''#!/bin/bash
                        set +e
                        mkdir -p logs reports
                        docker logs "payflex-perf-$BUILD_NUMBER" > logs/application-performance.log 2>&1
                        docker run --rm --user "$(id -u):$(id -g)" --volumes-from "$JENKINS_CONTAINER" \
                            "$GITLEAKS_IMAGE" detect --no-git --source "$PWD/logs" \
                            --config="$PWD/.gitleaks.toml" --report-format json \
                            --report-path "$PWD/gitleaks-performance-logs.json" --exit-code 0
                        python3 scripts/quality_gate.py secrets gitleaks-performance-logs.json
                        LOG_STATUS=$?
                        docker rm -f "payflex-perf-$BUILD_NUMBER" >/dev/null 2>&1
                        docker network rm "payflex-perf-$BUILD_NUMBER" >/dev/null 2>&1
                        exit "$LOG_STATUS"
                    '''
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'k6-summary.json,gitleaks-performance-logs.json,logs/**,reports/**'
                }
            }
        }

        stage('6 - Déploiement local') {
            when {
                expression {
                    env.BRANCH_NAME == 'main' || env.GIT_BRANCH == 'origin/main'
                }
            }
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail
                    docker network inspect payflex-production >/dev/null 2>&1 || docker network create payflex-production
                    docker rm -f payflex-production >/dev/null 2>&1 || true
                    docker run -d --restart unless-stopped --name payflex-production \
                        --network payflex-production -p 8000:8000 "$LOCAL_IMAGE"

                    for i in $(seq 1 30); do
                        if docker run --rm --network payflex-production "$CURL_IMAGE" -sf \
                            http://payflex-production:8000/health; then
                            echo 'Déploiement PayFlex validé'
                            exit 0
                        fi
                        sleep 1
                    done
                    exit 1
                '''
            }
            post {
                failure {
                    sh '''#!/bin/bash
                        mkdir -p reports
                        printf '# Rapport d incident\n\n**Étape** : déploiement\n\n- Le déploiement local ou le smoke test a échoué.\n' > reports/incident-deploy.md
                    '''
                }
                always {
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**'
                }
            }
        }
    }

    post {
        always {
            sh '''#!/bin/bash
                docker rm -f "payflex-extract-$BUILD_NUMBER" "payflex-it-$BUILD_NUMBER" \
                    "payflex-perf-$BUILD_NUMBER" "payflex-sonar-$BUILD_NUMBER" >/dev/null 2>&1 || true
                docker network rm "payflex-it-$BUILD_NUMBER" "payflex-perf-$BUILD_NUMBER" \
                    "payflex-sonar-$BUILD_NUMBER" >/dev/null 2>&1 || true
            '''
            archiveArtifacts allowEmptyArchive: true, artifacts: 'coverage.xml,k6-summary.json,sonar-measures.json,gitleaks-*.json,logs/**,reports/**'
        }
    }
}
