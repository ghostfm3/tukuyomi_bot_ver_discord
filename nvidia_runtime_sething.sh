# OSのディストリビューション情報
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)

# NVIDIA Dockerの公開鍵をダウンロード後にシステムに追加
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -

# NVIDIA Dockerのリポジトリ追加
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# パッケージリストを更新後にnvidia-docker2パッケージをインストール
sudo apt-get update && sudo apt-get install -y nvidia-docker2

# Dockerの再起動
sudo systemctl restart docker