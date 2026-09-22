pipeline {
    parameters {
        text(
            name: "config_overrides",
            // we check if the default value has been overrided from the interface
            defaultValue: params.config_overrides ?:"config:\n  random_seed: 1234",
            description: "Parts of yaml config to override, the default has no effect as it rewrite the same random seed"
        )
        string(
            name: "cache_server",
            defaultValue: params.cache_server ?:"false",
            description: "URL of the cache server to use, False not use any server"
        )
        string(
            name: "sampling_rates",
            defaultValue: params.sampling_rates ?:"0.001",
            description: "Space-separated list of sampling rates"
        )
        booleanParam(
            name: 'archive_outputs',
            defaultValue: params.archive_outputs ?:true,
            description: 'Whether you want to archive the outputs generated with the specified sampling rate'
        )
        booleanParam(
            name: 'archive_cache',
            defaultValue: params.archive_cache ?: false,
            description: 'Whether you want to archive the cache directory'
        )
        booleanParam(
            name: 'archive_data',
            defaultValue: params.archive_cache ?: false,
            description: 'Whether you want to archive the downloaded data used to generate the synthetic population'
        )
        booleanParam(
            name: 'archive_repo',
            defaultValue: params.archive_repo ?: false,
            description: 'Whether you want to archive the executed version of the repository'
        )
        string(
            name: 'download_retries',
            defaultValue: params.download_retries ?: "3",
            description: 'Number of times to retry downloading of necessary files in case of failure'
        )
    }

    agent {
        docker {
            image 'ghcr.io/eqasim-org/eqasim-france:main'
            args '  -i --entrypoint='
        }
    }

    stages {
        stage("Describe build") {
            steps {
                script {
                    currentBuild.description = sh(script: 'git log -1 --pretty=%B', returnStdout: true)
                    currentBuild.displayName = sh(script: 'git rev-parse --short HEAD', returnStdout: true)
                }
            }
        }

        stage('Prepare') {
            steps {
                sh '''
                BASE=$(pwd)
                # Making sure old directories are cleared
                rm -rf pipeline_data pipeline_cache pipeline_output

                mkdir pipeline_data
                mkdir pipeline_cache
                mkdir pipeline_output

                # Download yq to modify .yml files in command line
                python3 -c "import urllib.request; urllib.request.urlretrieve('https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64', 'yq')"
                chmod +x yq

                # Applying the overrides
                echo "$config_overrides" > overrides.yml
                uv --no-cache run scripts/override_config.py overrides.yml config.yml
                rm overrides.yml

                # setting up common cache and data path
                ./yq -i ".working_directory = \\"$BASE/pipeline_cache\\" | .config.data_path = \\"$BASE/pipeline_data\\" | .config.output_path = \\"$BASE/output_0.1pct\\" " config.yml
                '''
            }
        }

        stage('DownloadData') {
            options {
                /*
                Some times, when using a cache server, the timeout is reached before we start receiving data.
                In this case, the server keeps downloading so we can try again.
                */
                retry(params.download_retries as Integer)
            }
            steps {
                // We use uv with --no-cache to prevent it from writing into the home directory
                sh '''
                    rm -rf .home && mkdir .home
                    export HOME=$(pwd)/.home
                    uv --no-cache sync
                    uv --no-cache run scripts/download.py -y --requests verify=false --requests timeout=300 --cache-server "$cache_server" config.yml
                '''
            }
        }

        stage('Run') {
            steps {
                script {
                    def samplingRates = params.sampling_rates.tokenize()
                    for (def samplingRate in samplingRates) {
                        sh '''
                            samplingRate='''+samplingRate+'''
                            rm -rf "pipeline_output/output_${samplingRate}"
                            mkdir "pipeline_output/output_${samplingRate}"
                            uv --no-cache run -m synpp --config sampling_rate "${samplingRate}" --config output_path "pipeline_output/output_${samplingRate}" config.yml
                        '''
                    }
                }
            }
        }


        stage('Prepare artifacts') {
            steps {
                script {
                    if(params.archive_outputs) {
                    sh '''
                    cd pipeline_output
                    for i in *; do
                        echo "Archiving $i"
                        tar -czf "$i.tar.gz" $i/*
                    done
                    cd ..
                    '''
                    }

                    if(params.archive_cache) {
                        sh '''
                        tar -czf pipeline_cache.tar.gz pipeline_cache/*
                        '''
                    }

                    if(params.archive_data) {
                        sh '''
                        tar -czf pipeline_data.tar.gz pipeline_data/*
                        '''
                    }

                    if(params.archive_repo) {
                        sh '''
                        rm -rf .prepare_artifacts_temp
                        mkdir .prepare_artifacts_temp
                        mv pipeline_output .prepare_artifacts_temp/
                        mv pipeline_cache .prepare_artifacts_temp/
                        mv pipeline_data .prepare_artifacts_temp/
                        tar -czf repo.tar.gz *
                        mv .prepare_artifacts_temp/* /.
                        rm -rf .prepare_artifacts_temp
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                def artifacts = []
                if (params.archive_outputs) {
                    artifacts << 'pipeline_output/*'
                }

                if (params.archive_cache) {
                    artifacts << "pipeline_cache.tar.gz"
                }

                if (params.archive_data) {
                    artifacts << "pipeline_data.tar.gz"
                }

                if (params.archive_data) {
                    artifacts << "repo.tar.gz"
                }

                if (artifacts) {
                    archiveArtifacts artifacts: artifacts.join(','), fingerprint: true
                }
            }
        }
    }
}