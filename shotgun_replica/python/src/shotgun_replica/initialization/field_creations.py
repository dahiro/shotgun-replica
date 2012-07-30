from shotgun_api3 import Shotgun
import shotgun_api3
from elefant.utilities import config
from elefant.utilities.debug import debug
from elefant.utilities.definitions import INFO, DEBUG

conf = config.Configuration()

sg = Shotgun( conf.get( config.CONF_SHOTGUN_URL ),
              conf.get( config.CONF_SHOTGUN_SKRIPT ),
              conf.get( config.CONF_SHOTGUN_KEY ) );

addFields = []

# Parent Project for Project
addField = {}
addField["properties"] = {"summary_default":"none", "description":"Project this project arised from", "valid_types": ["Project"]}
addField["entity_type"] = "Project"
addField["data_typ"] = "entity"
addField["display_name"] = "Parent Project"
addFields.append( addField )

# Default tools for Step
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Default Tool for newly created Tasks"}
addField["entity_type"] = "Step"
addField["data_typ"] = "text"
addField["display_name"] = "Default Tool"
addFields.append( addField )

# Linked Entites
addField = {}
addField["properties"] = {"summary_default":"count",
                          "description":"Linked Shots",
                          "valid_types": ["Shot"]}
addField["entity_type"] = "Asset"
addField["data_typ"] = "multi_entity"
addField["display_name"] = "Linked Shots"
addFields.append( addField )

# Linked Entites
addField = {}
addField["properties"] = {"summary_default":"count",
                          "description":"Linked Assets",
                          "valid_types": ["Asset"]}
addField["entity_type"] = "Asset"
addField["data_typ"] = "multi_entity"
addField["display_name"] = "Linked Assets"
addFields.append( addField )

# Linked Entites
addField = {}
addField["properties"] = {"summary_default":"count",
                          "description":"Linked Shots",
                          "valid_types": ["Shot"]}
addField["entity_type"] = "Shot"
addField["data_typ"] = "multi_entity"
addField["display_name"] = "Linked Shots"
addFields.append( addField )

# Linked Entites
addField = {}
addField["properties"] = {"summary_default":"count",
                          "description":"Linked Assets",
                          "valid_types": ["Asset"]}
addField["entity_type"] = "Shot"
addField["data_typ"] = "multi_entity"
addField["display_name"] = "Linked Assets"
addFields.append( addField )

addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "X-Position in noodler"}
addField["entity_type"] = "Asset_sg_linked_assets_Connection"
addField["data_typ"] = "number"
addField["display_name"] = "posX"
addFields.append( addField )
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Y-Position in noodler"}
addField["entity_type"] = "Asset_sg_linked_assets_Connection"
addField["data_typ"] = "number"
addField["display_name"] = "posY"
addFields.append( addField )

addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "X-Position in noodler"}
addField["entity_type"] = "Shot_sg_linked_assets_Connection"
addField["data_typ"] = "number"
addField["display_name"] = "posX"
addFields.append( addField )
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Y-Position in noodler"}
addField["entity_type"] = "Shot_sg_linked_assets_Connection"
addField["data_typ"] = "number"
addField["display_name"] = "posY"
addFields.append( addField )

addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "X-Position in noodler"}
addField["entity_type"] = "Asset_sg_linked_shots_Connection"
addField["data_typ"] = "number"
addField["display_name"] = "posX"
addFields.append( addField )
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Y-Position in noodler"}
addField["entity_type"] = "Asset_sg_linked_shots_Connection"
addField["data_typ"] = "number"
addField["display_name"] = "posY"
addFields.append( addField )

addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "X-Position in noodler"}
addField["entity_type"] = "Shot_sg_linked_shots_Connection"
addField["data_typ"] = "number"
addField["display_name"] = "posX"
addFields.append( addField )
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Y-Position in noodler"}
addField["entity_type"] = "Shot_sg_linked_shots_Connection"
addField["data_typ"] = "number"
addField["display_name"] = "posY"
addFields.append( addField )


# List of files of Delivery
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Pipeline version restrictions"}
addField["entity_type"] = "Project"
addField["data_typ"] = "text"
addField["display_name"] = "pipelineVersion"
addFields.append( addField )

# Corresponding InOuts for PublishEvent
addField = {}
addField["properties"] = {"summary_default":"count", "description":"This output is used in these tasks", "valid_types": ["Task"]}
addField["entity_type"] = "CustomEntity02"
addField["data_typ"] = "multi_entity"
addField["display_name"] = "Sink Tasks"

addFields.append( addField )

# Corresponding Versions for InOut
addField = {}
addField["properties"] = {"summary_default":"count", "description":"Corresponding Versions for InOut", "valid_types": ["Version"]}
addField["entity_type"] = "CustomEntity02"
addField["data_typ"] = "multi_entity"
addField["display_name"] = "versions"

addFields.append( addField )

# Corresponding Task of InOut
addField = {}
addField["properties"] = {"summary_default":"count", "description":"Corresponding Task", "valid_types": ["Task"]}
addField["entity_type"] = "CustomEntity02"
addField["data_typ"] = "entity"
addField["display_name"] = "Link"

addFields.append( addField )

# Corresponding InOuts for PublishEvent
addField = {}
addField["properties"] = {"summary_default":"count", "description":"Corresponding InOuts", "valid_types": ["CustomEntity02"]}
addField["entity_type"] = "PublishEvent"
addField["data_typ"] = "multi_entity"
addField["display_name"] = "Corresponding InOuts"

addFields.append( addField )

# Tool Description for Task
addField = {}
addField["properties"] = {"summary_default":"count", "description":"Tool to be opened with", "valid_values": ["DummyTool"]}
addField["entity_type"] = "Task"
addField["data_typ"] = "list"
addField["display_name"] = "Tool"

addFields.append( addField )

# Type of InOut
addField = {}
addField["properties"] = {"summary_default":"count", "description":"Type of outputs", "valid_values": ["filesequence", "script", "playblast", "caches"]}
addField["entity_type"] = "CustomEntity02"
addField["data_typ"] = "list"
addField["display_name"] = "Type"

addFields.append( addField )

# Path of Task
addField = {}
addField["properties"] = {"summary_default":"count", "description":"Path where Files are stored"}
addField["entity_type"] = "Task"
addField["data_typ"] = "text"
addField["display_name"] = "Path"

addFields.append( addField )

# Path of Task
addField = {}
addField["properties"] = {"summary_default":"average", "description":"X-Position of task in node-editor"}
addField["entity_type"] = "Task"
addField["data_typ"] = "float"
addField["display_name"] = "choreo posx"

addFields.append( addField )

# Path of Task
addField = {}
addField["properties"] = {"summary_default":"average", "description":"Y-Position of task in node-editor"}
addField["entity_type"] = "Task"
addField["data_typ"] = "float"
addField["display_name"] = "choreo posy"

addFields.append( addField )

# remotely Updated by Fields
for entity in ["Sequence", "Shot", "Asset", "Task", "CustomEntity02", "CustomEntity03", "TaskTemplate"]:
    addField = {}
    addField["properties"] = {"summary_default":"none", "description":"Who did update from outside (mainly via couchdb)", "valid_types": ["HumanUser"]}
    addField["entity_type"] = entity
    addField["data_typ"] = "entity"
    addField["display_name"] = "Remotely Updated By"

    addFields.append( addField )

    addField = {}
    addField["properties"] = {"summary_default":"none", "description":"When the update from outside took place"}
    addField["entity_type"] = entity
    addField["data_typ"] = "date_time"
    addField["display_name"] = "Date Remote Update"

    addFields.append( addField )

for entity in ["Project", "Task", "CustomEntity02"]:
    addField = {}
    addField["properties"] = {"summary_default":"none", "description":"JSON Configuration settings"}
    addField["entity_type"] = entity
    addField["data_typ"] = "text"
    addField["display_name"] = "JSON conf"

    addFields.append( addField )

# output InOuts for Shot
addField = {}
addField["properties"] = {"summary_default":"count", "description":"Outputs of this Shot InOuts", "valid_types": ["CustomEntity02"]}
addField["entity_type"] = "Shot"
addField["data_typ"] = "multi_entity"
addField["display_name"] = "outputs"

addFields.append( addField )

# output InOuts for Asset
addField = {}
addField["properties"] = {"summary_default":"count", "description":"Outputs of this Asset InOuts", "valid_types": ["CustomEntity02"]}
addField["entity_type"] = "Asset"
addField["data_typ"] = "multi_entity"
addField["display_name"] = "outputs"

addFields.append( addField )

# output InOuts for Asset
addField = {}
addField["properties"] = {"summary_default":"sum",
                          "description":"Head In"}
addField["entity_type"] = "Asset"
addField["data_typ"] = "number"
addField["display_name"] = "Head In"

addFields.append( addField )

# output InOuts for Asset
addField = {}
addField["properties"] = {"summary_default":"sum",
                          "description":"Cut In"}
addField["entity_type"] = "Asset"
addField["data_typ"] = "number"
addField["display_name"] = "Cut In"

addFields.append( addField )

# output InOuts for Asset
addField = {}
addField["properties"] = {"summary_default":"sum",
                          "description":"Cut Out"}
addField["entity_type"] = "Asset"
addField["data_typ"] = "number"
addField["display_name"] = "Cut Out"

addFields.append( addField )

# output InOuts for Asset
addField = {}
addField["properties"] = {"summary_default":"sum",
                          "description":"Tail Out"}
addField["entity_type"] = "Asset"
addField["data_typ"] = "number"
addField["display_name"] = "Tail Out"

addFields.append( addField )

# output InOuts for TaskTemplate
addField = {}
addField["properties"] = {"summary_default":"count", "description":"Outputs of this TaskTemplate InOuts", "valid_types": ["CustomEntity02"]}
addField["entity_type"] = "TaskTemplate"
addField["data_typ"] = "multi_entity"
addField["display_name"] = "outputs"

addFields.append( addField )

# fps for project
addField = {}
addField["properties"] = {"summary_default":"none", "description":"Frame Rate (fps)"}
addField["entity_type"] = "Project"
addField["data_typ"] = "float"
addField["display_name"] = "Fps"

addFields.append( addField )

# units for project
addField = {}
addField["properties"] = {"summary_default":"none", "description":"Unit", "valid_values": ["millimeter", "centimeter", "meter", "kilometer", "inch", "foot", "yard", "mile"]}
addField["entity_type"] = "Project"
addField["data_typ"] = "list"
addField["display_name"] = "Unit"

addFields.append( addField )

# The used file format of the FormatLink
addField = {}
addField["properties"] = {"summary_default":"none", "description":"The used file format", "valid_types": ["CustomNonProjectEntity01"]}
addField["entity_type"] = "CustomEntity03"
addField["data_typ"] = "entity"
addField["display_name"] = "Format"
addFields.append( addField )

# The used format of the FormatLink
addField = {}
addField["properties"] = {"summary_default":"none", "description":"The used image size", "valid_types": ["CustomNonProjectEntity02"]}
addField["entity_type"] = "CustomEntity03"
addField["data_typ"] = "entity"
addField["display_name"] = "Size"
addFields.append( addField )

# The Usage type of the FormatLink
addField = {}
addField["properties"] = {"summary_default":"none", "description":"Format used for", "valid_values": ["scan", "projection", "work", "delivery", "preview"]}
addField["entity_type"] = "CustomEntity03"
addField["data_typ"] = "list"
addField["display_name"] = "Usage Type"
addFields.append( addField )

# wheater to add a slate frame or not
addField = {}
addField["properties"] = {"summary_default":"none", "description":"Add Slate Frame"}
addField["entity_type"] = "CustomEntity03"
addField["data_typ"] = "checkbox"
addField["display_name"] = "Add Slate Frame"
addFields.append( addField )

# wheater to add a overlay area around the image
addField = {}
addField["properties"] = {"summary_default":"none", "description":"wheater to add a overlay area around the image"}
addField["entity_type"] = "CustomEntity03"
addField["data_typ"] = "checkbox"
addField["display_name"] = "Add Overlay"
addFields.append( addField )

# wheater to add a overlay area around the image
addField = {}
addField["properties"] = {"summary_default":"none", "description":"wheater to crop image"}
addField["entity_type"] = "CustomEntity03"
addField["data_typ"] = "checkbox"
addField["display_name"] = "Crop Image"
addFields.append( addField )

# Crop X
addField = {}
addField["properties"] = {"summary_default":"none", "description":"crop x coordinate"}
addField["entity_type"] = "CustomEntity03"
addField["data_typ"] = "number"
addField["display_name"] = "Crop X"
addFields.append( addField )

# Crop Y
addField = {}
addField["properties"] = {"summary_default":"none", "description":"crop y coordinate"}
addField["entity_type"] = "CustomEntity03"
addField["data_typ"] = "number"
addField["display_name"] = "Crop Y"
addFields.append( addField )

# Crop R
addField = {}
addField["properties"] = {"summary_default":"none", "description":"crop r coordinate"}
addField["entity_type"] = "CustomEntity03"
addField["data_typ"] = "number"
addField["display_name"] = "Crop R"
addFields.append( addField )

# Crop T
addField = {}
addField["properties"] = {"summary_default":"none", "description":"crop t coordinate"}
addField["entity_type"] = "CustomEntity03"
addField["data_typ"] = "number"
addField["display_name"] = "Crop T"
addFields.append( addField )

# Filetype extension of Format
addField = {}
validValues = ["tga", "jpg", "dpx", "cin", "exr", "tif", "mov", "wmv", "sgi"]
validValues.sort()
addField["properties"] = {"summary_default":"none", "description":"Extensions of File(s)", "valid_values": validValues}
addField["entity_type"] = "CustomNonProjectEntity01"
addField["data_typ"] = "list"
addField["display_name"] = "Filetype extension"
addFields.append( addField )


# Colorspace of Format
addField = {}
addField["properties"] = {"summary_default":"none", "description":"Colorspace of Format", "valid_values": ["default", "linear", "log", "sRGB", "rec709", "Cineon"]}
addField["entity_type"] = "CustomNonProjectEntity01"
addField["data_typ"] = "list"
addField["display_name"] = "Colorspace"

addFields.append( addField )


# Datatype with bit-depth
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Datatype with bit-depth",
                          "valid_values": ["int 8bit", "int 10bit", "int 12bit", "int 16bit", "float 16bit", "float 32bit"]}
addField["entity_type"] = "CustomNonProjectEntity01"
addField["data_typ"] = "list"
addField["display_name"] = "Datatype"
addFields.append( addField )


# Storage Type
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Storage type",
                          "valid_values": ["imagesequence", "movie"]}
addField["entity_type"] = "CustomNonProjectEntity01"
addField["data_typ"] = "list"
addField["display_name"] = "Storage type"
addFields.append( addField )


# Compression attributes
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Compression attributes"}
addField["entity_type"] = "CustomNonProjectEntity01"
addField["data_typ"] = "text"
addField["display_name"] = "Compression attributes"
addFields.append( addField )


# Width
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Width"}
addField["entity_type"] = "CustomNonProjectEntity02"
addField["data_typ"] = "number"
addField["display_name"] = "Width"
addFields.append( addField )


# Height
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Height"}
addField["entity_type"] = "CustomNonProjectEntity02"
addField["data_typ"] = "number"
addField["display_name"] = "Height"
addFields.append( addField )


# Pixel ratio
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Pixel ratio"}
addField["entity_type"] = "CustomNonProjectEntity02"
addField["data_typ"] = "float"
addField["display_name"] = "Pixel ratio"
addFields.append( addField )

# Link for FormatLink
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Link for FormatLink",
                          "valid_types": ["CustomEntity02",
                                          "Task",
                                          "Shot",
                                          "Sequence",
                                          "Asset"]}
addField["entity_type"] = "CustomEntity03"
addField["data_typ"] = "entity"
addField["display_name"] = "Link"
addFields.append( addField )


# Compression attributes
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Choosen Output format"}
addField["entity_type"] = "CustomEntity02"
addField["data_typ"] = "text"
addField["display_name"] = "Output Format Link"
addFields.append( addField )


# Compression attributes
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Use this name for imports"}
addField["entity_type"] = "CustomEntity02"
addField["data_typ"] = "text"
addField["display_name"] = "import as"
addFields.append( addField )


# InOut->sink_tasks fields
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "How many times something gets imported"}
addField["entity_type"] = "CustomEntity02_sg_sink_tasks_Connection"
addField["data_typ"] = "number"
addField["display_name"] = "Import Count"
addFields.append( addField )


# InOut->sink_tasks fields
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Flag wheather this output is imported"}
addField["entity_type"] = "CustomEntity02_sg_sink_tasks_Connection"
addField["data_typ"] = "checkbox"
addField["display_name"] = "Is imported"
addFields.append( addField )


# locking of a task 
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Who holds the lock",
                          "valid_types": ["HumanUser"]}
addField["entity_type"] = "Task"
addField["data_typ"] = "entity"
addField["display_name"] = "Locked by"
addFields.append( addField )

# locking of a task 
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "date and time of lock creation/release"}
addField["entity_type"] = "Task"
addField["data_typ"] = "date_time"
addField["display_name"] = "Locked at"
addFields.append( addField )


# InOut->sink_tasks fields
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Version that has been imported"}
addField["entity_type"] = "CustomEntity02_sg_sink_tasks_Connection"
addField["data_typ"] = "text"
addField["display_name"] = "versionImported"
addFields.append( addField )

# InOut->sink_tasks fields
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "json conf data"}
addField["entity_type"] = "CustomEntity02_sg_sink_tasks_Connection"
addField["data_typ"] = "text"
addField["display_name"] = "JSON conf"
addFields.append( addField )

# Minor Version stuff
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Comment"}
addField["entity_type"] = "CustomEntity04"
addField["data_typ"] = "text"
addField["display_name"] = "comment"
addFields.append( addField )

# Minor Version stuff
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Comment"}
addField["entity_type"] = "CustomEntity04"
addField["data_typ"] = "text"
addField["display_name"] = "published"
addFields.append( addField )

# Minor Version stuff
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "Derived From"}
addField["entity_type"] = "CustomEntity04"
addField["data_typ"] = "text"
addField["display_name"] = "derivedFrom"
addFields.append( addField )

# Minor Version stuff
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "filepath"}
addField["entity_type"] = "CustomEntity04"
addField["data_typ"] = "text"
addField["display_name"] = "filepath"
addFields.append( addField )

# Minor Version stuff
addField = {}
addField["properties"] = {"summary_default": "none",
                          "description": "scriptpath"}
addField["entity_type"] = "CustomEntity04"
addField["data_typ"] = "text"
addField["display_name"] = "scriptpath"
addFields.append( addField )

# Corresponding Task of MinorVersion
addField = {}
addField["properties"] = {"summary_default":"count", "description":"Corresponding Task", "valid_types": ["Task"]}
addField["entity_type"] = "CustomEntity04"
addField["data_typ"] = "entity"
addField["display_name"] = "Link"
addFields.append( addField )

# remotely Updated by Fields
for entity in ["Shot", "Asset", "Project", "CustomEntity01", "Sequence"]:
    addField = {}
    addField["properties"] = {"summary_default":"none",
                              "description":"Where the files are stored (relative)"}
    addField["entity_type"] = entity
    addField["data_typ"] = "text"
    addField["display_name"] = "Path"

    addFields.append( addField )

# Corresponding InOut of Delivery
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Corresponding Node-Container",
                          "valid_types": ["Project", "Sequence", "Shot", "Asset"]}

addField["entity_type"] = "CustomEntity01"
addField["data_typ"] = "entity"
addField["display_name"] = "Link"
addFields.append( addField )

# Corresponding InOut of Delivery
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Corresponding InOut",
                          "valid_types": ["CustomEntity02"]}

addField["entity_type"] = "CustomEntity30"
addField["data_typ"] = "entity"
addField["display_name"] = "inout"
addFields.append( addField )

# Corresponding InOut of Delivery
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Corresponding Version",
                          "valid_types": ["Version"]}

addField["entity_type"] = "CustomEntity30"
addField["data_typ"] = "entity"
addField["display_name"] = "Version"
addFields.append( addField )

# Corresponding PublishEvent of Delivery
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Corresponding PublishEvent",
                          "valid_types": ["PublishEvent"]}

addField["entity_type"] = "CustomEntity30"
addField["data_typ"] = "entity"
addField["display_name"] = "publishEvent"
addFields.append( addField )

# List of files of Delivery
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Corresponding Files"}
addField["entity_type"] = "CustomEntity30"
addField["data_typ"] = "text"
addField["display_name"] = "fileList"
addFields.append( addField )

# List of files of Delivery
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Base name for files of Tasks in Shot"}
addField["entity_type"] = "Shot"
addField["data_typ"] = "text"
addField["display_name"] = "basename"
addFields.append( addField )

# List of files of Delivery
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Path to frames from windows"}
addField["entity_type"] = "Version"
addField["data_typ"] = "text"
addField["display_name"] = "Path to Frames windows"
addFields.append( addField )

# List of files of Delivery
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Base name for files of Tasks in Asset"}
addField["entity_type"] = "Asset"
addField["data_typ"] = "text"
addField["display_name"] = "basename"
addFields.append( addField )

# List of files of Delivery
addField = {}
addField["properties"] = {"summary_default":"none",
                          "description":"Client of this project",
                          "valid_types": ["CustomNonProjectEntity15"]}
addField["entity_type"] = "Project"
addField["data_typ"] = "entity"
addField["display_name"] = "client"
addFields.append( addField )

def makeSgName( name ):
    name = name.lower()
    name = name.replace( " ", "_" )
    return "sg_" + name

for addField in addFields:
    debug( "checking field: %s (%s) for Entity %s" % ( makeSgName( addField["display_name"] ), addField["display_name"], addField["entity_type"] ), DEBUG )
    try:
        result = sg.schema_field_read( addField["entity_type"], makeSgName( addField["display_name"] ) )
    except shotgun_api3.Fault, e:
        debug( "   creating field", INFO )
        createdField = sg.schema_field_create( addField["entity_type"], addField["data_typ"], addField["display_name"], addField["properties"] )

