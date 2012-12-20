Name: libmysqlclient16
Version: 5.1.65
Release: 1%{?dist}
Summary: The shared libraries required for MySQL clients
Group: Applications/Databases
URL: http://www.mysql.com
# exceptions allow client libraries to be linked with most open source SW,
# not only GPL code.  See README.mysql-license
License: GPLv2 with exceptions

# Upstream has a mirror redirector for downloads, so the URL is hard to
# represent statically.  You can get the tarball by following a link from
# http://dev.mysql.com/downloads/mysql/
Source0: mysql-%{version}-nodocs.tar.gz
# The upstream tarball includes non-free documentation that we cannot ship.
# To remove the non-free documentation, run this script after downloading
# the tarball into the current directory:
# ./generate-tarball.sh $VERSION
Source1: generate-tarball.sh
Source4: scriptstub.c
Source5: my_config.h
Source7: README.mysql-license
# Working around perl dependency checking bug in rpm FTTB. Remove later.
Source999: filter-requires-mysql.sh

Patch1: mysql-ssl-multilib.patch
Patch2: mysql-errno.patch
Patch4: mysql-testing.patch
Patch5: mysql-install-test.patch
Patch6: mysql-stack-guard.patch
Patch8: mysql-setschedparam.patch
Patch9: mysql-no-docs.patch
Patch12: mysql-cve-2008-7247.patch
Patch13: mysql-expired-certs.patch
Patch16: mysql-chain-certs.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Prereq: /sbin/ldconfig, /sbin/install-info, grep, fileutils
BuildRequires: gperf, perl, readline-devel, openssl-devel
BuildRequires: gcc-c++, ncurses-devel, zlib-devel
BuildRequires: libtool automake autoconf gawk

Requires: bash

# Working around perl dependency checking bug in rpm FTTB. Remove later.
%global __perl_requires %{SOURCE999}

# Force include and library files into a nonstandard place
%{expand: %%define _origincludedir %{_includedir}}
%{expand: %%define _origlibdir %{_libdir}}
%define _includedir %{_origincludedir}/%{name}
%define _libdir %{_origlibdir}/%{name}

%description
The libmysqlclient16 package provides the essential shared libraries for any 
MySQL client program or interface. You will need to install this package
to use any other MySQL package or any clients that need to connect to a
MySQL server.

%package devel

Summary: Files for development of MySQL applications
Group: Applications/Databases
Requires: %{name} = %{version}-%{release}
Requires: openssl-devel
Conflicts: MySQL-devel

%description devel
MySQL is a multi-user, multi-threaded SQL database server. This
package contains the libraries and header files that are needed for
developing MySQL client applications.

%prep
%setup -q -n mysql-%{version}

%patch1 -p1
%patch2 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch8 -p1
%patch9 -p1
%patch12 -p1
%patch13 -p1
%patch16 -p1

libtoolize --force
aclocal
automake --add-missing -Wno-portability
autoconf
autoheader

%build
CFLAGS="%{optflags} -D_GNU_SOURCE -D_FILE_OFFSET_BITS=64 -D_LARGEFILE_SOURCE"
# MySQL 4.1.10 definitely doesn't work under strict aliasing; also,
# gcc 4.1 breaks MySQL 5.0.16 without -fwrapv
CFLAGS="$CFLAGS -fno-strict-aliasing -fwrapv"
# force PIC mode so that we can build libmysqld.so
CFLAGS="$CFLAGS -fPIC"
# gcc seems to have some bugs on sparc as of 4.4.1, back off optimization
# submitted as bz #529298
%ifarch sparc sparcv9 sparc64
CFLAGS=`echo $CFLAGS| sed -e "s|-O2|-O1|g" `
%endif
# extra C++ flags as per recommendations in mysql's INSTALL-SOURCE doc
CXXFLAGS="$CFLAGS -felide-constructors -fno-rtti -fno-exceptions"
export CFLAGS CXXFLAGS

# mysql 5.1.30 fails regression tests on x86 unless we use --with-big-tables,
# suggesting that upstream doesn't bother to test the other case ...
# note: the with-plugin and without-plugin options do actually work; ignore
# warnings from configure suggesting they are ignored ...
%configure \
	--with-readline \
	--with-ssl=/usr \
	--without-debug \
	--enable-shared \
	--without-bench \
	--without-server \
	--without-docs \
	--without-man \
	--localstatedir=/var/lib/mysql \
	--with-unix-socket-path=/var/lib/mysql/mysql.sock \
	--with-mysqld-user="mysql" \
	--with-extra-charsets=all \
	--enable-local-infile \
	--enable-largefile \
	--enable-thread-safe-client \
	--disable-dependency-tracking

gcc $CFLAGS $LDFLAGS -o scriptstub "-DLIBDIR=\"%{_libdir}/mysql\"" %{SOURCE4}

# Not enabling assembler

make %{?_smp_mflags}
make check

%install
rm -rf $RPM_BUILD_ROOT

%makeinstall

# multilib header hacks
# we only apply this to known Red Hat multilib arches, per bug #181335
case `uname -i` in
  i386 | x86_64 | ppc | ppc64 | s390 | s390x | sparc | sparc64 )
    mv $RPM_BUILD_ROOT%{_includedir}/mysql/my_config.h $RPM_BUILD_ROOT%{_includedir}/mysql/my_config_`uname -i`.h
    install -m 644 %{SOURCE5} $RPM_BUILD_ROOT%{_includedir}/mysql/
    ;;
  *)
    ;;
esac

mv ${RPM_BUILD_ROOT}%{_bindir}/mysql_config ${RPM_BUILD_ROOT}%{_libdir}/mysql/mysql_config

# We want the .so files both in regular _libdir (for execution) and
# in special _libdir/mysql4 directory (for convenient building of clients).
# The ones in the latter directory should be just symlinks though.
mkdir -p ${RPM_BUILD_ROOT}%{_origlibdir}/mysql
pushd ${RPM_BUILD_ROOT}%{_origlibdir}/mysql
mv -f ${RPM_BUILD_ROOT}%{_libdir}/mysql/libmysqlclient.so.16.*.* .
mv -f ${RPM_BUILD_ROOT}%{_libdir}/mysql/libmysqlclient_r.so.16.*.* .
cp -p -d ${RPM_BUILD_ROOT}%{_libdir}/mysql/libmysqlclient*.so.* .
popd
pushd ${RPM_BUILD_ROOT}%{_libdir}/mysql
ln -s ../../mysql/libmysqlclient.so.16.*.* .
ln -s ../../mysql/libmysqlclient_r.so.16.*.* .
popd

rm -rf $RPM_BUILD_ROOT%{_prefix}/mysql-test
rm -f ${RPM_BUILD_ROOT}%{_libdir}/mysql/*.{a,la}
rm -rf $RPM_BUILD_ROOT%{_datadir}/mysql
rm -rf $RPM_BUILD_ROOT%{_bindir}
rm -rf $RPM_BUILD_ROOT%{_prefix}/sql-bench
rm -rf $RPM_BUILD_ROOT%{_datadir}/aclocal/mysql.m4

mkdir -p $RPM_BUILD_ROOT/etc/ld.so.conf.d
echo "%{_origlibdir}/mysql" > $RPM_BUILD_ROOT/etc/ld.so.conf.d/%{name}-%{_arch}.conf

# copy additional docs into build tree so %%doc will find them
cp %{SOURCE7} README.mysql-license

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/ldconfig

%postun
if [ $1 = 0 ] ; then
    /sbin/ldconfig
fi

%files
%defattr(-,root,root)
%doc README COPYING README.mysql-license
%{_origlibdir}/mysql/libmysqlclient*.so.*
/etc/ld.so.conf.d/*

%files devel
%defattr(-,root,root)
%{_includedir}/mysql
%{_libdir}/mysql/libmysqlclient*.so
%{_libdir}/mysql/libmysqlclient*.so.*
%{_libdir}/mysql/mysql_config

%changelog
* Thu Dec 20 2012 Andy Thompson <andy@webtatic.com> 5.1.65-1
- Update to mysql-5.1.65

* Tue Dec 21 2010 Andy Thompson <andy@webtatic.com> 5.1.54-1
- Initial build
