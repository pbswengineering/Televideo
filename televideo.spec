Summary: Italian RAI Televideo viewer
Name: televideo
Version: 1.1
Release: 1
License: MIT
Group: Applications/Network
URL: http://paolobernardi.wordpress.com/
Vendor: Paolo Bernardi
Packager: Paolo Bernardi <bernarpa@gmail.com>
BuildArch: noarch
Requires: python, pygtk2, ImageMagick

%description
With this software you can browse the RAI Televideo
easily from your Linux Desktop. Cool eh? The Televideo
content is written in Italian.

%prep
rm -fr Televideo
git clone https://github.com/bernarpa/Televideo

%build
cd Televideo
make

%install
cd Televideo
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

%files
/usr/share/doc/televideo/AUTHORS
/usr/share/doc/televideo/COPYING
/usr/share/doc/televideo/README
/usr/share/televideo/televideo.py
/usr/share/televideo/loading.png
/usr/share/televideo/not-found.png
/usr/share/televideo/televideo.xml
/usr/share/televideo/televideo.svg
/usr/bin/televideo
/usr/share/applications/televideo.desktop

%clean
rm -fr Televideo
rm -fr %{buildroot}

%changelog
* Wed Jul 6 2011 Paolo Bernardi <bernarpa@gmail.com> 1.1-1
- Initial package
