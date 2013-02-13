# -*- coding: utf-8 -*-

## @package shotgun_replica
# Synchronization of Shotgun with local Postgresql
#
#

import re

UNKNOWN_SHOTGUN_ID = -1

def cleanSysName(name):
    """ replace non-normal char or whitespace with capital following character
    english this good being"""
    
    def whitespacerepl(match):
        """replace whitespaces with Capital"""
        return match.group(0).upper()
    
    stage1 = re.sub(r"[^a-zA-Z0-9_]([a-zA-Z])", whitespacerepl, name)
    cleanName = re.sub(r"[^a-zA-Z0-9\_]", '', stage1)
    
    return cleanName
