#!/usr/bin/python
#coding:utf-8


def _mac():
  import random

  maclist = []
  for i in range(7):
    randstr = ''.join(random.sample('1234567890abcdef',2))
    maclist.append(randstr)
  randmac = ':'.join(maclist)
  return randmac

def _uuid():
  import uuid
  
  return uuid.uuid1()

def _parse_xml(tag):
  import xml.dom.minidom

  basic_xml = '/home/wangpei/centos7-basic.xml'
  dom = xml.dom.minidom.parse(basic_xml)
  root = dom.documentElement
  name = root.getElementsByTagName(tag)[0]
  return name


def _make_xml(name):
  import os,stat,sys
  import re

  basic_xml = '/home/wangpei/centos7-basic.xml'
  vm_xml = '/etc/libvirt/qemu/' + name + '.xml'
  image = '/vm/kvm/centos7-basic.img'

  if os.path.exists(vm_xml):
    print '{0} is exist'.format(vm_xml)
    sys.exit()

  with open(basic_xml,'r') as fd_r,open(vm_xml,'w+') as fd_w:
    vm_name = _parse_xml('name').firstChild.data
    vm_uuid = _parse_xml('uuid').firstChild.data
    vm_desc = _parse_xml('description').firstChild.data
    vm_image = _parse_xml('source').getAttribute('file')
    uuid = str(_uuid())
    for line in fd_r.readlines():
      if vm_name in line:
        line = re.sub(vm_name,name,line)
      elif vm_uuid in line:
        line = re.sub(vm_uuid,uuid,line)
      elif vm_desc in line:
        line = re.sub(vm_desc,desc,line)
      elif vm_image in line:
        line = re.sub(vm_image,image,line)
      fd_w.write(line)
  os.chmod(vm_xml,stat.S_IRUSR|stat.S_IWUSR)

def _make_image(name):
  import shutil,sys
  import os
  
  basic_img = '/vm/kvm/centos7-basic.img'
  vm_image = '/vm/kvm/' + name + '.img'
  if os.path.exists(vm_image):
    print "{0} is exist".format(vm_image)
    sys.exit()
  shutil.copy(basic_img,vm_image)

def _conn_dom():
  import libvirt

  conn = libvirt.open('qemu:///system')
  return conn

def _make_ifcfg(ip):
  niclist = []
  niclist.append('IPADDR="{0}"'.format(ip))
  niclist.append('GATEWAY="192.168.100.1"')
  niclist.append('NETMASK="255.255.255.0"')
  niclist.append('BOOTPROTO="static"')
  niclist.append('DEVICE="eth0"')
  niclist.append('ONBOOT="yes"')
  niclist.append('DNS1="8.8.8.8"')
  with open('/tmp/ifcfg-eth0','w+') as f:
    for nic in niclist:
      f.write(nic + '\n')

def _upload_file(name):
  import subprocess,shlex
  
  cmd = "virt-copy-in -d {0} {1} {2}".format(name,'/tmp/ifcfg-eth0','/etc/sysconfig/network-scripts/')
  cmd = shlex.split(cmd)
  p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
  p.communicate()

def create_vm(name,ip):
  import libvirt
  import os,sys

  vm_xml = '/etc/libvirt/qemu/' + name + '.xml'
  vm_image = '/vm/kvm/' + name + '.img'
  if not os.path.exists(vm_xml):
    _make_xml(name)
  if not os.path.exists(vm_image):
    _make_image(name)

  conn = _conn_dom()
  if conn.lookupByName(name) == None:
    with open(vm_xml) as f:
      xml = f.read() 
      conn.defineXML(xml)
      conn.close()
  else:
    print '{0} is exist'.format(name)
    return

  _make_ifcfg(ip)
  if os.path.exists('/tmp/ifcfg-eth0'):
    _upload_file(name)
    os.remove('/tmp/ifcfg-eth0')


def start_vm(name):
  import libvirt
  import sys

  conn = _conn_dom()
  try:
    dom = conn.lookupByName(name) 
    if name in conn.listDefinedDomains():
      dom.create()
      conn.close()
    else:
      print '{0} is running'.format(name)
      return
  except Exception as e:
    print e

def stop_vm(name):
  import libvirt

  conn = _conn_dom()
  try:
    dom = conn.lookupByName(name)
    if name not in conn.listDefinedDomains():
      dom.destroy()
      conn.close()
    else:
      print '{0} is not running'.format(name)
      return
  except Exception as e:
    print e 

def undefine_vm(name):
  import libvirt

  conn = _conn_dom()
  try:
    dom = conn.lookupByName(name)
    dom.undefine()
    conn.close()
  except Exception as e:
    print e

if __name__ == '__main__':
  import sys
  #input vm name
  name = sys.argv[1] 
  #input vm ip
  desc = sys.argv[2]
 
  if sys.argv[3] == 'create_vm': 
    create_vm(name,desc)
  elif sys.argv[3] == 'start_vm':
    start_vm(name)
  elif sys.argv[3] == 'stop_vm':
    stop_vm(name)
  elif sys.argv[3] == 'undefine_vm':
    undefine_vm(name)
