Summary:	A firewall administration web interface
Name:		nuface
Version:	2.0.14
Release:	%mkrel 4
License:	GPL
Group:		System/Servers
URL:		http://software.inl.fr/trac/wiki/EdenWall/NuFace
Source0:	http://software.inl.fr/releases/Nuface/%{name}-%{version}.tar.bz2
Patch0:		nuface-docmake.patch
Patch1:		nuface-make1.patch
Patch2:   	nuface-manualrules-targets.patch
Requires(pre):	php-ldap sudo
Requires:	webserver php-ldap sudo libxml2-python python-ldap gettext nuphp sudo
Suggests:       mod_ssl nufw-utils
Requires:	python python-pygraphviz graphviz iproute2 net-tools python-IPy php-pear-Image_GraphViz
Requires(post): rpm-helper
Requires(preun): rpm-helper
BuildRequires:	python python-devel
BuildRequires:	ImageMagick libxslt-proc docbook-style-xsl docbook-dtd45-xml
BuildRequires:	apache-base >= 2.0.54
Requires(post):	ccp >= 0.4.0
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot


%description
Nuface2 is an intuitive firewall configuration interface for EdenWall/NuFW as
well as for Netfilter. It lets you use high level objects, agglomerate objects
into ACLs, and deals with generating Netfilter rules as well as LDAP Acls for
NuFW.

%prep

%setup -q
%patch0 -p0
%patch1 -p0
%patch2 -p1

%build
make all

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

install -d %{buildroot}%{_initrddir}
install -d %{buildroot}%{_sysconfdir}/httpd/conf/webapps.d
install -d %{buildroot}%{_sysconfdir}/%{name}
install -d %{buildroot}%{_localstatedir}/lib/%{name}
install -d %{buildroot}/var/log/%{name}
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}/var/www/%{name}
install -d %{buildroot}%{_datadir}/%{name}
install -d %{buildroot}%{_docdir}/%{name}

%makeinstall_std

install AUTHORS BUGS COPYING Changelog INSTALL README %{buildroot}%{_docdir}/%{name}
install README.* %{buildroot}%{_docdir}/%{name}
cp -a doc/nuface %{buildroot}%{_docdir}/%{name}
install doc/ck-style.css %{buildroot}%{_docdir}/%{name}
install doc/desc.* %{buildroot}%{_docdir}/%{name}
install doc/acls.dtd %{buildroot}%{_docdir}/%{name}
install doc/empty.xml %{buildroot}%{_docdir}/%{name}
install doc/*.rst %{buildroot}%{_docdir}/%{name}
install doc/desc.xml %{buildroot}/var/lib/nuface/desc.xml.ex

echo -e "<?php\ninclude (\"/etc/nuface/config.php\"); \n?>" > %{buildroot}/var/www/nuface/include/config.php

cat > %{buildroot}%{_sysconfdir}/httpd/conf/webapps.d/%{name}.conf << EOF

Alias /%{name} /var/www/%{name}

<Directory /var/www/%{name}>
    Allow from All
    # Create this file with "htpasswd -c %{_sysconfdir}/%{name}/apache_users username"
    Authtype Basic
    AuthName "Nuface authentication"
    AuthUserFile %{_sysconfdir}/%{name}/apache_users
    Require valid-user
    php_flag allow_call_time_pass_reference on
    ErrorDocument 401 "The password you entered was incorrect, or the username you used has not been configured. New users can be added by running htpasswd -c %{_sysconfdir}/%{name}/apache_users username"
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

# Mandriva Icons
install -d %{buildroot}%{_iconsdir}
install -d %{buildroot}%{_miconsdir}
install -d %{buildroot}%{_liconsdir}

convert images/nupik.png -resize 16x16 %{buildroot}%{_miconsdir}/%{name}.png
convert images/nupik.png -resize 32x32 %{buildroot}%{_iconsdir}/%{name}.png
convert images/nupik.png -resize 48x48 %{buildroot}%{_liconsdir}/%{name}.png

# install menu entry.
install -d %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/mandriva-%{name}.desktop << EOF
[Desktop Entry]
Name=Nuface
Comment=A firewall administration web interface.
Exec=/usr/bin/www-browser https://localhost/%{name}
Icon=%{name}
Terminal=false
Type=Application
StartupNotify=true
Categories=System;Monitor;
EOF

%post
%_post_service init-firewall
ccp --delete --ifexists --set "NoOrphans" --ignoreopt config_version --oldfile %{_sysconfdir}/%{name}/config.php --newfile %{_sysconfdir}/%{name}/config.php.rpmnew
%_post_webapp

%postun
%_postun_webapp

%preun
%_preun_service init-firewall

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc *
%doc %{_var}/lib/nuface/local_rules.d/README
%doc %{_var}/lib/nuface/desc.xml.ex
%attr(0755,root,root) /etc/init.d/init-firewall
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/webapps.d/%{name}.conf
%config %dir %attr(0755,apache,apache) %{_var}/lib/%{name}
%config %dir %attr(0755,apache,apache) %{_var}/lib/%{name}/dyn
%config %dir %attr(0755,apache,apache) %{_var}/lib/%{name}/dyn/nufw
%config %dir %attr(0755,apache,apache) %{_var}/lib/%{name}/dyn/standard
%config %dir %attr(0755,apache,apache) %{_var}/lib/nuface/local_rules.d
%config %dir %attr(0755,apache,apache) %{_var}/lib/%{name}/acls
%config %dir %attr(0755,root,root) %{_var}/lib/%{name}/backups
%config(noreplace) %attr(0644,root,apache) /etc/nuface/config.php
%config(noreplace) %attr(0644,root,apache) /etc/nuface/nupyf.conf
%config %{_var}/lib/nuface/acls/fixed/empty.xml
%dir %attr(0755,root,root) %{_var}/log/%{name}
# main app files
%{_var}/www/%{name}
# python
%{py_sitedir}

%{_datadir}/applications/mandriva*.desktop
%{_datadir}/locale/fr/LC_MESSAGES/nuface.mo
%{_mandir}
%{_sbindir}
%{_iconsdir}/%{name}.png
%{_miconsdir}/%{name}.png
%{_liconsdir}/%{name}.png
