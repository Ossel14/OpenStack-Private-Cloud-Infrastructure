terraform {
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 1.53.0"
    }
  }
}

# Terraform will automatically use the credentials from your 'openrc' file
provider "openstack" {}

resource "openstack_compute_instance_v2" "centos_vm" {
  name        = "Terraform-CentOS-VM"
  image_name  = "CentOS-7"
  flavor_name = "m1.custom"

  network {
    name = "private"
  }

  # THIS IS THE MAGIC TRICK: Bypasses the broken DevStack metadata network
  config_drive = true

  # This script runs automatically when the VM boots up
  user_data = <<-EOF
              #!/bin/bash
              # Set the password for the centos user
              echo "centos:ur password" | chpasswd

              # Force the SSH server to allow password logins
              sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config

              # Restart the SSH service to apply the changes
              systemctl restart sshd
              EOF
}
