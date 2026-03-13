resource "hcloud_server" "bot-danubio" {
  count       = var.instances
  name        = "bot-danubio-${count.index}"
  image       = var.os_type
  server_type = var.server_type
  location    = var.location
  labels = {
    type = "web"
  }
  user_data    = file("terraform.yaml")
  ssh_keys     = ["rsa-key-20171111", "monitchat"]
  firewall_ids = [1114609]

  network {
    network_id = 3536266
  }

  provisioner "file" {
    source      = "~/.ssh/id_rsa"
    destination = "/home/bot/.ssh/id_rsa"

    connection {
      type        = "ssh"
      user        = "bot"
      private_key = file("/home/luiz-ricardo/keys/monitchat")
      host        = self.ipv4_address
    }

  }

  provisioner "file" {
    source      = "${path.root}/../../.env.prod"
    destination = "/home/bot/.env"

    connection {
      type        = "ssh"
      user        = "bot"
      private_key = file("/home/luiz-ricardo/keys/monitchat")
      host        = self.ipv4_address
    }

  }

  provisioner "file" {
    source      = "~/.ssh/id_rsa.pub"
    destination = "/home/bot/.ssh/id_rsa.pub"

    connection {
      type        = "ssh"
      user        = "bot"
      private_key = file("/home/luiz-ricardo/keys/monitchat")
      host        = self.ipv4_address
    }

  }

  provisioner "file" {
    content     = "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl\ngithub.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg=\ngithub.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk="
    destination = "/home/bot/.ssh/known_hosts"

    connection {
      type        = "ssh"
      user        = "bot"
      private_key = file("/home/luiz-ricardo/keys/monitchat")
      host        = self.ipv4_address
    }
  }

  provisioner "remote-exec" {
    inline = [
      "sudo add-apt-repository universe -y",
      "sudo DEBIAN_FRONTEND=noninteractive apt install python3-pip -y",
      "sudo DEBIAN_FRONTEND=noninteractive apt install python3.12-venv -y  ",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y build-essential && apt-get install -y libpq-dev",
      "sudo chmod 600 /home/bot/.ssh/id_rsa",
      "cd /home/bot",
      "GIT_SSH_COMMAND=\"ssh -i /home/bot/.ssh/id_rsa\" git clone git@github.com:monitchat/bot-danubio.git",
      "mv /home/bot/.env /home/bot/bot-danubio",
      ". /home/bot/bot-danubio/.env",
      "cd /home/bot/bot-danubio",
      "docker compose up -d pgbouncer rabbitmq",
      "sleep 10",
      "tests/resources/database/seed-database.sh",
      "docker compose up -d app",
      "sleep 5"
    ]

    connection {
      type        = "ssh"
      user        = "bot"
      private_key = file("/home/luiz-ricardo/keys/monitchat")
      host        = self.ipv4_address
    }
  }
}
