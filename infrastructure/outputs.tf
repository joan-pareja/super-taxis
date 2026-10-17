output "image_repository" {
  description = "Push application images under this Artifact Registry path."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}

output "app_url" {
  description = "Public HTTPS URL for the demo application."
  value       = try(google_cloud_run_v2_service.app[0].uri, null)
}
