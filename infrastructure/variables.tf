variable "project_id" {
  description = "Existing Google Cloud project with billing enabled."
  type        = string
}

variable "credentials_file" {
  description = "Path to the local Google login JSON file, relative to the infrastructure folder."
  type        = string
}

variable "region" {
  description = "Region shared by the application, database and image repository."
  type        = string
  default     = "europe-west1"
}

variable "app_image" {
  description = "Built app image in Artifact Registry. Leave null to provision supporting resources first."
  type        = string
  default     = null

  validation {
    condition     = var.app_image == null || can(regex("@sha256:[a-f0-9]{64}$", var.app_image))
    error_message = "Use an immutable image reference ending in @sha256:<digest>."
  }
}

variable "database_password" {
  description = "Database password from the ignored terraform.tfvars; not stored in Terraform state or plan files."
  type        = string
  sensitive   = true
  ephemeral   = true

  validation {
    condition     = can(regex("^[A-Za-z0-9_-]{24,128}$", var.database_password))
    error_message = "Use 24-128 letters, digits, underscores or hyphens so the password is safe in the dotenv file."
  }
}

variable "database_password_version" {
  description = "Increase when changing the password to update both Cloud SQL and Secret Manager."
  type        = number
  default     = 1
}

variable "protect_database" {
  description = "Prevent deleting the database instance until deliberately set to false and applied."
  type        = bool
  default     = true
}
