FROM technic93/e2xvfb:latest

RUN rev="acac722e25a5e2d69d60d4df6bcef701049e2b38" \
 && curl -fsSL https://github.com/littlesat/skin-PLiHD/archive/$rev.zip -o skin-PLiHD.zip \
 && unzip skin-PLiHD.zip && cd skin-PLiHD-$rev && sudo cp -arv . /

RUN sudo apt-get update && sudo apt-get install -y \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-libav

# friendly shell
RUN sudo apt-get install -y bash-completion command-not-found psmisc
