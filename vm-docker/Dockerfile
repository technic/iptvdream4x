FROM technic93/e2xvfb:latest

RUN rev="acac722e25a5e2d69d60d4df6bcef701049e2b38" \
 && curl -fsSL https://github.com/littlesat/skin-PLiHD/archive/$rev.zip -o skin-PLiHD.zip \
 && unzip skin-PLiHD.zip && cd skin-PLiHD-$rev && sudo cp -arv . /

RUN sudo apt-get update && sudo apt-get install -y \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-libav

RUN sudo apt-get install -y bash-completion command-not-found psmisc htop vim wput

RUN echo "config.skin.primary_skin=PLi-HD/skin.xml" >> /etc/enigma2/settings \
 && echo "config.misc.do_overscanwizard=false" >> /etc/enigma2/settings

# See: https://github.com/Microsoft/ptvsd/pull/1403
# RUN sudo pip install ptvsd
RUN pip install git+https://github.com/technic/ptvsd.git@patch-1
EXPOSE 5678
COPY mytest-ptvsd.py /opt/mytest-ptvsd.py
CMD [ "x11vnc", "-forever" ]
