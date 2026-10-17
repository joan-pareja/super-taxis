locals {
  name       = "super-taxis"
  deploy_app = var.app_image != null

  # Keep the same explicit dotenv loading as the local application.
  database_settings = join("\n", [
    "POSTGRES_DB=${google_sql_database.app.name}",
    "POSTGRES_USER=${google_sql_user.app.name}",
    "POSTGRES_PASSWORD=${var.database_password}",
    "POSTGRES_HOST=/cloudsql/${google_sql_database_instance.app.connection_name}",
    "POSTGRES_PORT=5432",
    "",
  ])
}

resource "google_project_service" "api" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = local.name
  format        = "DOCKER"
  description   = "Versioned application images for Super Taxis."

  depends_on = [google_project_service.api]
}

resource "google_sql_database_instance" "app" {
  name                = "${local.name}-db"
  region              = var.region
  database_version    = "POSTGRES_18"
  deletion_protection = var.protect_database

  settings {
    tier                        = "db-f1-micro"
    edition                     = "ENTERPRISE"
    availability_type           = "ZONAL"
    disk_size                   = 10
    disk_type                   = "PD_SSD"
    deletion_protection_enabled = var.protect_database

    # The Cloud SQL Auth Proxy secures the connection; no direct IP allowlist is added.
    ip_configuration {
      ipv4_enabled = true
      ssl_mode     = "ENCRYPTED_ONLY"
    }

    backup_configuration {
      enabled = true
    }
  }

  depends_on = [google_project_service.api]
}

resource "google_sql_database" "app" {
  name     = "taxi"
  instance = google_sql_database_instance.app.name
}

resource "google_sql_user" "app" {
  name                = "taxi"
  instance            = google_sql_database_instance.app.name
  password_wo         = var.database_password
  password_wo_version = var.database_password_version
}

resource "google_service_account" "app" {
  account_id   = local.name
  display_name = "Super Taxis application"

  depends_on = [google_project_service.api]
}

resource "google_project_iam_member" "database_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.app.email}"
}

resource "google_secret_manager_secret" "database" {
  secret_id = "${local.name}-database"

  replication {
    auto {}
  }

  depends_on = [google_project_service.api]
}

resource "google_secret_manager_secret_version" "database" {
  secret                 = google_secret_manager_secret.database.id
  secret_data_wo         = local.database_settings
  secret_data_wo_version = var.database_password_version
}

resource "google_secret_manager_secret_iam_member" "database_reader" {
  secret_id = google_secret_manager_secret.database.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

resource "google_cloud_run_v2_service" "app" {
  count = local.deploy_app ? 1 : 0

  name                 = local.name
  location             = var.region
  deletion_protection  = false
  invoker_iam_disabled = true

  template {
    service_account                  = google_service_account.app.email
    execution_environment            = "EXECUTION_ENVIRONMENT_GEN2"
    max_instance_request_concurrency = 20

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    containers {
      image   = var.app_image
      command = ["sh", "-c"]
      # Match the local demo: prepare the database before serving requests.
      args = [join(" && ", [
        "cp /secrets/database/settings.env /app/.env",
        "alembic upgrade head",
        "python -m app.seed",
        "exec uvicorn app.main:app --host 0.0.0.0 --port 8000",
      ])]

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }

      volume_mounts {
        name       = "database-settings"
        mount_path = "/secrets/database"
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    volumes {
      name = "database-settings"
      secret {
        secret = google_secret_manager_secret.database.secret_id
        items {
          version = google_secret_manager_secret_version.database.version
          path    = "settings.env"
        }
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.app.connection_name]
      }
    }
  }

  depends_on = [
    google_project_iam_member.database_client,
    google_secret_manager_secret_iam_member.database_reader,
  ]
}
