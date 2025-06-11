# 📦 Instalação do Docker

## Para executar o Sistema de Contabilidade com Agentes

### 🖥️ Windows

#### 1. Baixar Docker Desktop
- Acesse: https://docs.docker.com/desktop/install/windows/
- Baixe o **Docker Desktop for Windows**
- Execute o instalador como Administrador

#### 2. Requisitos Windows
- Windows 10/11 Pro/Enterprise/Education
- WSL 2 habilitado (o instalador configura automaticamente)
- Virtualização habilitada no BIOS

#### 3. Verificar Instalação
```cmd
docker --version
docker-compose --version
```

### 🐧 Linux (Ubuntu/Debian)

#### 1. Instalar Docker
```bash
# Atualizar sistema
sudo apt update

# Instalar dependências
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# Adicionar chave GPG oficial
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar repositório
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io
```

#### 2. Instalar Docker Compose
```bash
# Baixar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Dar permissão de execução
sudo chmod +x /usr/local/bin/docker-compose
```

#### 3. Configurar usuário
```bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Reiniciar sessão ou executar
newgrp docker
```

### 🍎 macOS

#### 1. Baixar Docker Desktop
- Acesse: https://docs.docker.com/desktop/install/mac/
- Baixe **Docker Desktop for Mac** (Intel ou Apple Silicon)
- Instale o arquivo .dmg

#### 2. Verificar Instalação
```bash
docker --version
docker-compose --version
```

### 🔧 Após Instalação

#### 1. Verificar se está funcionando
```bash
docker run hello-world
```

#### 2. Configurar recursos (opcional)
- **Windows/Mac**: Docker Desktop > Settings > Resources
- **Recomendado**: 
  - RAM: 4GB mínimo (8GB ideal)
  - CPU: 2 cores mínimo (4 cores ideal)
  - Disk: 20GB para imagens

### ⚡ Executar Sistema

Após instalação, volte ao diretório do projeto e:

**Windows:**
```cmd
start_docker.bat
```

**Linux/Mac:**
```bash
./start_docker.sh
```

### 🐛 Troubleshooting

#### Windows
- **Erro WSL 2**: Execute `wsl --install` no PowerShell como Admin
- **Virtualização**: Habilite VT-x/AMD-V no BIOS
- **Hyper-V**: Pode precisar ser habilitado no "Recursos do Windows"

#### Linux
- **Permissão negada**: Certifique-se que usuário está no grupo docker
- **Service não inicia**: `sudo systemctl start docker`

#### macOS
- **Recursos insuficientes**: Aumente RAM/CPU no Docker Desktop

### 📚 Links Úteis
- [Documentação Docker](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Troubleshooting Docker Desktop](https://docs.docker.com/desktop/troubleshoot/)

---
**Após instalação**: Execute `QUICK_START_DOCKER.md` para usar o sistema! 