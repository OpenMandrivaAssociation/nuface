Summary:	A firewall administration web interface
Name:		nuface
Version:	1.0.5
Release:	%mkrel 2
License:	GPL
Group:		System/Servers
URL:		http://www.inl.fr/Nuface.html
Source0:	http://www.inl.fr/download/%{name}-%{version}.tar.bz2
Source1:	nupyf.init.bz2
Patch0:		nuface-1.0.5-mdv_config.diff
Requires(pre):	apache-mod_php apache-mod_ssl php-ldap sudo
Requires:	apache-mod_php apache-mod_ssl php-ldap sudo
Requires(post): rpm-helper
Requires(preun): rpm-helper
BuildRequires:	python
BuildRequires:	dos2unix
BuildRequires:	ImageMagick
BuildRequires:	apache-base >= 2.0.54
Requires(post):	ccp >= 0.4.0
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
Nuface is an intuitive firewall configuration interface for EdenWall/NuFW as
well as for Netfilter. It lets you use high level objects, agglomerate objects
into ACLs, and deals with generating Netfilter rules as well as LDAP Acls for
NuFW.

%prep

%setup -q
%patch0 -p1

# clean up CVS stuff
for i in `find . -type d -name CVS` `find . -type f -name .cvs\*` `find . -type f -name .#\*`; do
    if [ -e "$i" ]; then rm -r $i; fi >&/dev/null
done

# fix dir perms
find . -type d | xargs chmod 755

# fix file perms
find . -type f | xargs chmod 644

# strip away annoying ^M
find -type f | grep -v "\.gif" | grep -v "\.png" | grep -v "\.jpg" | xargs dos2unix -U

bzcat %{SOURCE1} > nupyf.init

%build

pushd scripts
    python setup_nupyf.py build
popd

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

export DONT_RELINK=1

install -d %{buildroot}%{_initrddir}
install -d %{buildroot}%{_sysconfdir}/httpd/conf/webapps.d
install -d %{buildroot}%{_sysconfdir}/%{name}
install -d %{buildroot}%{_sysconfdir}/%{name}/dyn
install -d %{buildroot}%{_sysconfdir}/%{name}/dyn/nufw
install -d %{buildroot}%{_sysconfdir}/%{name}/dyn/standard
install -d %{buildroot}%{_sysconfdir}/%{name}/desc
install -d %{buildroot}%{_localstatedir}/%{name}
install -d %{buildroot}/var/log/%{name}
install -d %{buildroot}%{_sbindir}

install -d %{buildroot}/var/www/%{name}
install -d %{buildroot}%{_datadir}/%{name}

cp -aRf * %{buildroot}/var/www/%{name}/

install -m0755 nupyf.init %{buildroot}%{_initrddir}/nupyf

install doc/desc.xml %{buildroot}%{_sysconfdir}/%{name}/desc/desc.xml.ex
install doc/acls.xml %{buildroot}%{_localstatedir}/%{name}/empty.xml
install scripts/nupyf.conf %{buildroot}%{_sysconfdir}/%{name}/desc/desc.xml.ex

install scripts/nupyf.conf %{buildroot}%{_sysconfdir}/%{name}/desc/nupyf.conf

pushd scripts
    python setup_nupyf.py install --root %{buildroot} --install-purelib=%{py_sitedir}
popd

cat > run_nupyf << EOF
#!/bin/sh
exec %{_bindir}/python %{py_sitedir}/nupyf/nupyf.py \$*
EOF

install -m0755 run_nupyf %{buildroot}%{_sbindir}/nupyf

# cleanup
pushd %{buildroot}/var/www/%{name}
    rm -rf debian scripts
    rm -f AUTHORS BUGS COPYING Changelog INSTALL README TODO nupyf.init
    rm -f images/*.xcf install.sh
    find -name "\.htaccess" | xargs rm -f
    find -name "Makefile" | xargs rm -f
popd

# fix python permissions
pushd %{buildroot}%{py_sitedir}/nupyf
    find -type f -name "*.py*" | xargs chmod 755
popd

# fix config file location
mv %{buildroot}/var/www/%{name}/include/config.php %{buildroot}%{_sysconfdir}/%{name}/config.php

# fix apache config
cat > %{buildroot}%{_sysconfdir}/httpd/conf/webapps.d/%{name}.conf << EOF

Alias /%{name} /var/www/%{name}

<Directory /var/www/%{name}>
    Allow from All
    # Create this file with "htpasswd -c %{_sysconfdir}/%{name}/apache_users username"
    Authtype Basic
    AuthName "Nuface authentication"
    AuthUserFile %{_sysconfdir}/%{name}/apache_users
    Require valid-user
</Directory>

<Directory /var/www/%{name}/include>
    Order Deny,Allow
    Deny from All
    Allow from None
</Directory>

<LocationMatch /%{name}>
    Options FollowSymLinks
    RewriteEngine on
    RewriteCond %{SERVER_PORT} !^443$
    RewriteRule ^.*$ https://%{SERVER_NAME}%{REQUEST_URI} [L,R]
</LocationMatch>

EOF

# install script to call the web interface from the menu.
install -d %{buildroot}%{_libdir}/%{name}/scripts
cat > %{buildroot}%{_libdir}/%{name}/scripts/%{name} <<EOF
#!/bin/sh

url='https://localhost/%{name}'
if ! [ -z "\$BROWSER" ] && ( which \$BROWSER ); then
  browser=\`which \$BROWSER\`
elif [ -x /usr/bin/mozilla-firefox ]; then
  browser=/usr/bin/mozilla-firefox
elif [ -x /usr/bin/konqueror ]; then
  browser=/usr/bin/konqueror
elif [ -x /usr/bin/lynx ]; then
  browser='xterm -bg black -fg white -e lynx'
elif [ -x /usr/bin/links ]; then
  browser='xterm -bg black -fg white -e links'
else
  xmessage "No web browser found, install one or set the BROWSER environment variable!"
  exit 1
fi
\$browser \$url
EOF
chmod 755 %{buildroot}%{_libdir}/%{name}/scripts/%{name}

# Mandriva Icons
install -d %{buildroot}%{_iconsdir}
install -d %{buildroot}%{_miconsdir}
install -d %{buildroot}%{_liconsdir}

convert nupik.png -resize 16x16 %{buildroot}%{_miconsdir}/%{name}.png
convert nupik.png -resize 32x32 %{buildroot}%{_iconsdir}/%{name}.png
convert nupik.png -resize 48x48 %{buildroot}%{_liconsdir}/%{name}.png

# install menu entry.
install -d %{buildroot}%{_menudir}
cat > %{buildroot}%{_menudir}/%{name} << EOF
?package(%{name}): needs=X11 \
section="System/Monitoring" \
title="Nuface" \
longtitle="A firewall administration web interface.  Set the $BROWSER environment variable to choose your preferred browser." \
command="%{_libdir}/%{name}/scripts/%{name} 1>/dev/null 2>/dev/null" \
icon="%{name}.png"
EOF

%post
%_post_service nupyf
ccp --delete --ifexists --set "NoOrphans" --ignoreopt config_version --oldfile %{_sysconfdir}/%{name}/config.php --newfile %{_sysconfdir}/%{name}/config.php.rpmnew
%_post_webapp
%update_menus

%postun
%_postun_webapp
%clean_menus

%preun
%_preun_service nupyf

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc AUTHORS BUGS COPYING Changelog INSTALL README
%attr(0755,root,root) %{_initrddir}/nupyf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/webapps.d/%{name}.conf
%dir %attr(0755,root,root) %{_sysconfdir}/%{name}
%dir %attr(0755,root,root) %{_sysconfdir}/%{name}/dyn
%dir %attr(0755,root,root) %{_sysconfdir}/%{name}/dyn/nufw
%dir %attr(0755,root,root) %{_sysconfdir}/%{name}/dyn/standard
%dir %attr(0755,root,root) %{_sysconfdir}/%{name}/desc
%dir %attr(0755,root,root) %{_localstatedir}/%{name}
%dir %attr(0755,root,root) /var/log/%{name}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/desc/desc.xml.ex
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/desc/nupyf.conf
%attr(0644,root,root) %config(noreplace) %{_localstatedir}/%{name}/empty.xml
%attr(0755,root,root) %{_sbindir}/nupyf
%attr(0640,apache,root) %config(noreplace) %{_sysconfdir}/%{name}/config.php
/var/www/%{name}
%{py_sitedir}/nupyf
%attr(0755,root,root) %{_libdir}/%{name}/scripts/%{name}
%{_menudir}/%{name}
%{_iconsdir}/%{name}.png
%{_miconsdir}/%{name}.png
%{_liconsdir}/%{name}.png

