.PHONY: all clean install uninstall

all:
	@echo "It's all there, just an ls away!"

clean:
	rm -f *~

install:
	mkdir -p $(DESTDIR)/usr/share/televideo/
	cp televideo.py loading.png not-found.png televideo.xml televideo.svg $(DESTDIR)/usr/share/televideo/
	mkdir -p $(DESTDIR)/usr/share/doc/televideo/
	cp AUTHORS COPYING README $(DESTDIR)/usr/share/doc/televideo/
	test -d $(DESTDIR)/usr/bin/ || mkdir -p $(DESTDIR)/usr/bin/
	ln -s $(DESTDIR)/usr/share/televideo/televideo.py $(DESTDIR)/usr/bin/televideo
	test -d $(DESTDIR)/usr/share/applications/ || mkdir -p $(DESTDIR)/usr/share/applications/
	cp televideo.desktop $(DESTDIR)/usr/share/applications/
	update-desktop-database || true

uninstall:
	rm -f $(DESTDIR)/usr/bin/televideo
	rm -fr $(DESTDIR)/usr/share/televideo/
	rm -fr $(DESTDIR)/usr/share/doc/televideo/
	rm -f $(DESTDIR)/usr/share/applications/televideo.desktop
	update-desktop-database || true
