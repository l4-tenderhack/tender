function Get-ComposeCommand {
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        return "docker-compose"
    }

    try {
        docker compose version | Out-Null
        return "docker compose"
    }
    catch {
        throw "Docker Compose is not installed. Install docker compose plugin or docker-compose."
    }
}

$compose = Get-ComposeCommand
Invoke-Expression "$compose run --rm app pytest"
