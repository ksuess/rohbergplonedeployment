from batou import UpdateNeeded
from batou.component import Component, Attribute
from batou.lib.cmmi import Build
from batou.lib.file import File
from batou.lib.python import VirtualEnv
from batou.utils import Address

# TODO -n name individually

class Varnish(Component):

    address = Attribute(Address, '127.0.0.1:11090')
    control_port = Attribute(int, '11091')
    daemon = ''
    daemonargs = ''

    def configure(self):
        self.provide('varnish:http', self)
        self.purgehosts = self.require('zope:http')
        self.voltoapp = self.require_one('voltoapp')
        self.haproxy = self.require_one('haproxy:frontend')
        
        self += VirtualEnv('3.7')

        self += Build(
            'https://varnish-cache.org/_downloads/e2a305a110260371a068ba3f22f10233/varnish-6.5.1.tgz',
            checksum='sha256:11964c688f9852237c99c1e327d54dc487549ddb5f0f5aa7996e521333d7cdb5',
        )
        self += File('websiteplone.vcl', source='websiteplone.vcl')
        self.daemon = 'sbin/varnishd'
        self.daemonargs = self.expand(
                '-F -f {{component.workdir}}/websiteplone.vcl '
                '-T localhost:{{component.control_port}} '
                '-a {{component.address.listen}} '
                '-p thread_pool_min=10 '
                '-p thread_pool_max=50 '
                '-s malloc,250M '
                '-n websitesomething'
            )
        print("varnish self.daemon", self.daemon)

        self += PurgeCache()


class PurgeCache(Component):

    varnishadm = 'bin/varnishadm'

    def verify(self):
        raise UpdateNeeded()

    def update(self):
        self.cmd(self.expand(
            '{{component.varnishadm}}'
            ' -S {{component.workdir}}/var/varnish/websitesomething/_.secret'
            ' -T "localhost:{{component.parent.control_port}}"'
            ' "ban req.url ~ .*"'),
            ignore_returncode=True
        )
