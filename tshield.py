# -*- coding: UTF-8 -*-

"""
TODO
    vf_body_contains support Chinese
"""

from __future__ import division             # 3.x //
from __future__ import generators
from __future__ import nested_scopes
from __future__ import with_statement       # with/as, needed in 2.5
from __future__ import print_function       # 3.x print
from __future__ import absolute_import
from __future__ import unicode_literals     # 3.x string

import yaml # pyyaml
import requests # requests
from hamcrest import * # pyhamcrest

################## Test YAML String ############################################

tc_str = """
---
config       : 
    desc     : "初始化默认配置"             
    http     :
        addr : dev.yypm.com
    mysql    :
        addr : localhost:3306
---
http        :
    desc    : 访问根路径，返回码应为200
    do_get  : /
    vf_code : 200
    vf_body_contains: updateplf
---
mysql         :
    desc      : 初始化数据
    do_insert : insert into `user` values('a', 'b');
    vf_result : success
"""

################## YAML Customize (need orderDict) #############################

import yaml
import yaml.constructor

from collections import OrderedDict     # 2.7

class OrderedDictYAMLLoader(yaml.Loader):
    """ See https://gist.github.com/enaeseth/844388 (with updates) """
 
    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)
        self.add_constructor(u'tag:yaml.org,2002:map', type(self).construct_yaml_map)   # the std mapping syntax
        self.add_constructor(u'tag:yaml.org,2002:omap', type(self).construct_yaml_map)  # the "!omap" syntax
 
    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)
 
    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(None, None,
                'expected a mapping node, but found %s' % node.id, node.start_mark)
 
        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError, exc:
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                    node.start_mark, 'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping
 

################################################################################

DESC = "desc"
PREFIX_DO = "do_"
PREFIX_VF = "vf_"

def getActionClass(name):
    # getattr(tshield, actionType) / globals()[actionType]() / locals()[actionType]()
    return globals().get(name.title())

class Action:
    def __init__(self, actionData):
        self.actionData = OrderedDict(actionData.items() + self.__class__.config.items())

    def perform(self):
        Action.desc(self)
        for k in self.actionData : 
            if k.startswith(PREFIX_DO) or k.startswith(PREFIX_VF):
                getattr(self, k)(self.actionData[k])
        print("\tAll Success")

    def desc(self):
        print("\n{}\t{}".format(self.__class__.__name__, self.actionData.get(DESC)))

class Config(Action):
    config = {}
    def perform(self):
        Action.desc(self)
        for actionType in self.actionData:
            clazz = getActionClass(actionType)
            if clazz: clazz.config.update(self.actionData[actionType])

class Http(Action):
    config = {}
    def do_get(self, data):
        url = "http://{}{}".format(self.actionData["addr"], data)
        print("\tHTTP GET request to: {}".format(url))
        self.result = requests.get(url)

    def vf_code(self, data):
        print("\tVerify response status code, exepct: {}".format(data))
        (self.result.status_code, equal_to(data))

    def vf_body_contains(self, data):
        print("\tVerify response body, exepct contains: {}".format(data))
        assert_that(self.result.text, contains_string(data))

class Mysql(Action):
    config = {}
    def do_insert(self, data):
        print("---------------do_insert {}".format(data))

    def vf_result(self, data):
        print("---------------vf_result {} ".format(data))

################################################################################

if __name__ == "__main__" : 
    import textwrap

    #for actionDef in yaml.load_all(tc_str):
    #for actionDef in yaml.load_all(textwrap.dedent(tc_str), OrderedDictYAMLLoader):
    for actionDef in yaml.load_all(tc_str, OrderedDictYAMLLoader):
        actionType = actionDef.keys()[0]
        actionData = actionDef.values()[0]
        action = getActionClass(actionType)(actionData)
        action.perform()

