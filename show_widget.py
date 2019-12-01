import sys, os
from collections import OrderedDict
# import random
from PySide2.QtGui import QGuiApplication
from PySide2.QtCore import QObject, QUrl, Slot, QStringListModel, Property, Signal, QTimer
from PySide2.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide2.QtGui import QIcon
# # compiled QML files, compile with pyside2-rcc
# import qml.qml
os.environ["QT_IM_MODULE"] = "qtvirtualkeyboard"
import icons.icons
# #, imagine_assets
import resource_rc

import patch_bay_model
import ingen_wrapper

# def insert_row(model, row):
#     j = len(model.stringList())
#     model.insertRows(j, 1)
#     model.setData(model.index(j), row)
current_source_port = None
# current_effects = OrderedDict()
current_effects = {}
# current_effects["delay1"] = {"x": 20, "y": 30, "effect_type": "delay", "controls": {}, "highlight": False}
# current_effects["delay2"] = {"x": 250, "y": 290, "effect_type": "delay", "controls": {}, "highlight": False}
port_connections = {} # key is port, value is list of ports

context = None

patch_bay_model.local_effects = current_effects
    # effect = {"parameters", "inputs", "outputs", "effect_type", "id", "x", "y"}
effect_prototypes ={
        "input": {"inputs": {},
        "outputs": {"out": "AudioPort"},
        "controls": {}},
        "output": {"inputs": {"in": "AudioPort"},
        "outputs": {},
        "controls": {}},
        "delay": {"inputs": {"in0": "AudioPort"},
        "outputs": {"out0": "AudioPort"},
        "controls": {"BPM_0" : ["BPM_0", 120.000000, 30.000000, 300.000000],
            "Delay_1" : ["Time", 0.500000, 0.001000, 4.000000],
            "Warp_2" : ["Warp", 0.000000, -1.000000, 1.000000],
            "DelayT60_3" : ["Glide", 0.500000, 0.000000, 100.000000],
            "Feedback_4" : ["Feedback", 0.300000, 0.000000, 1.000000],
            "Amp_5" : ["Level", 0.500000, 0.000000, 1.000000],
            "FeedbackSm_6" : ["Tone", 0.000000, 0.000000, 1.000000],
            "EnableEcho_7" : ["EnableEcho_7", 1.000000, 0.000000, 1.000000]}
        },
        # "mixer":  {"inputs": {"in0": "AudioPort"},
        # "outputs": {"out0": "AudioPort"},
        # "controls":{"mix_1_1": ["mix 1,1", 1, 0, 1], "mix_1_2": ["mix 1,2", 0, 0, 1],
        #     "mix_1_3": ["mix 1,3", 0, 0, 1],"mix_1_4": ["mix 1,4", 0, 0, 1],
        #     "mix_2_1": ["mix 2,1", 0, 0, 1],"mix_2_2": ["mix 2,2", 1, 0, 1],
        #     "mix_2_3": ["mix 2,3", 0, 0, 1],"mix_2_4": ["mix 2,4", 0, 0, 1],
        #     "mix_3_1": ["mix 3,1", 0, 0, 1],"mix_3_2": ["mix 3,2", 0, 0, 1],
        #     "mix_3_3": ["mix 3,3", 1, 0, 1],"mix_3_4": ["mix 3,4", 0, 0, 1],
        #     "mix_4_1": ["mix 4,1", 0, 0, 1],"mix_4_2": ["mix 4,2", 0, 0, 1],
        #     "mix_4_3": ["mix 4,3", 0, 0, 1],"mix_4_4": ["mix 4,4", 1, 0, 1]
        #     },
        "warmth": {"inputs": {"input": "AudioPort"},
                "outputs": {"output": "AudioPort"},
            "controls":{"drive": ["drive", 5, 0, 10], "blend": ["tape vs tube", 10, -10, 10]},
            },
        "mono_reverb": {"inputs": {"in": "AudioPort"},
                "outputs": {"out": "AudioPort"},
                "controls":{"gain": ["gain", 0, -24, 24], "ir": ["/audio/reverbs/emt_140_dark_1.wav", 0, 0, 1]},
            },
        "stereo_reverb": {"inputs": {"in": "AudioPort"},
            "outputs": {"out_1": "AudioPort", "out_2": "AudioPort"},
                "controls":{"gain": ["gain", 0, -24, 24], "ir": ["/audio/reverbs/emt_140_dark_1.wav", 0, 0, 1]},
            },
        "true_stereo_reverb": {"inputs": {"in_1": "AudioPort", "in_2": "AudioPort"},
            "outputs": {"out_1": "AudioPort", "out_2": "AudioPort"},
                "controls":{"gain": ["gain", 0, -24, 24], "ir": ["/audio/reverbs/emt_140_dark_1.wav", 0, 0, 1]},
            },
        "mono_cab": {"inputs": {"in": "AudioPort"},
                "outputs": {"out": "AudioPort"},
                "controls":{"gain": ["gain", 0, -24, 24], "ir": ["/audio/cabs/1x12cab.wav", 0, 0, 1]},
            },
        "stereo_cab": {"inputs": {"in": "AudioPort"},
            "outputs": {"out_1": "AudioPort", "out_2": "AudioPort"},
                "controls":{"gain": ["gain", 0, -24, 24], "ir": ["/audio/cabs/1x12cab.wav", 0, 0, 1]},
            },
        "true_stereo_cab": {"inputs": {"in_1": "AudioPort", "in_2": "AudioPort"},
            "outputs": {"out_1": "AudioPort", "out_2": "AudioPort"},
                "controls":{"gain": ["gain", 0, -24, 24], "ir": ["/audio/cabs/1x12cab.wav", 0, 0, 1]},
            },
        # "filter1": {"freq": ["cutoff", 440, 20, 15000, "log"], "res": ["resonance", 0, 0, 0.8]},
        "saturator": {"inputs": {"input": "AudioPort"},
            "outputs": {"output": "AudioPort"},
            "controls":{"Pregain": ["pre gain", 0, -90, 20], "Postgain": ["post gain", 0, -90, 20]},
            },
        "reverse": {"inputs": {"input": "AudioPort"},
            "outputs": {"output": "AudioPort"},
            "controls":{"fragment": ["fragment", 1000, 100, 1600],
                "wet": ["wet", 0, -90, 20],
                "dry": ["dry", 0, -90, 20]},
            },
        "mono_EQ": {"inputs": {"In": "AudioPort"},
            "outputs": {"Out": "AudioPort"},
            "controls": {
                "enable": ["Enable", 1.000000, 0.000000, 1.0],
                "gain": ["Gain", 0.000000, -18.000000, 18.000000],
                "HighPass": ["Highpass", 0.000000, 0.000000, 1.000000],
                "HPfreq": ["Highpass Frequency", 20.000000, 5.000000, 1250.000000],
                "HPQ": ["HighPass Resonance", 0.700000, 0.000000, 1.400000],
                "LowPass": ["Lowpass", 0.000000, 0.000000, 1.000000],
                "LPfreq": ["Lowpass Frequency", 20000.000000, 500.000000, 20000.000000],
                "LPQ": ["LowPass Resonance", 1.000000, 0.000000, 1.400000],
                "LSsec": ["Lowshelf", 1.000000, 0.000000, 1.000000],
                "LSfreq": ["Lowshelf Frequency", 80.000000, 25.000000, 400.000000],
                "LSq": ["Lowshelf Bandwidth", 1.000000, 0.062500, 4.000000],
                "LSgain": ["Lowshelf Gain", 0.000000, -18.000000, 18.000000],
                "sec1": ["Section 1", 1.000000, 0.000000, 1.000000],
                "freq1": ["Frequency 1", 160.000000, 20.000000, 2000.000000],
                "q1": ["Bandwidth 1", 0.600000, 0.062500, 4.000000],
                "gain1": ["Gain 1", 0.000000, -18.000000, 18.000000],
                "sec2": ["Section 2", 1.000000, 0.000000, 1.000000],
                "freq2": ["Frequency 2", 397.000000, 40.000000, 4000.000000],
                "q2": ["Bandwidth 2", 0.600000, 0.062500, 4.000000],
                "gain2": ["Gain 2", 0.000000, -18.000000, 18.000000],
                "sec3": ["Section 3", 1.000000, 0.000000, 1.000000],
                "freq3": ["Frequency 3", 1250.000000, 100.000000, 10000.000000],
                "q3": ["Bandwidth 3", 0.600000, 0.062500, 4.000000],
                "gain3": ["Gain 3", 0.000000, -18.000000, 18.000000],
                "sec4": ["Section 4", 1.000000, 0.000000, 1.000000],
                "freq4": ["Frequency 4", 2500.000000, 200.000000, 20000.000000],
                "q4": ["Bandwidth 4", 0.600000, 0.062500, 4.000000],
                "gain4": ["Gain 4", 0.000000, -18.000000, 18.000000],
                "HSsec": ["Highshelf", 1.000000, 0.000000, 1.000000],
                "HSfreq": ["Highshelf Frequency", 8000.000000, 1000.000000, 16000.000000],
                "HSq": ["Highshelf Bandwidth", 1.000000, 0.062500, 4.000000],
                "HSgain": ["Highshelf Gain", 0.000000, -18.000000, 18.000000]}
            },
        "stereo_EQ": {"inputs": {"inR": "AudioPort", "inL": "AudioPort"},
            "outputs": {"outR": "AudioPort", "outL": "AudioPort"},
            "controls": {
                "enable": ["Enable", 1.000000, 0.000000, 1.0],
                "gain": ["Gain", 0.000000, -18.000000, 18.000000],
                "HighPass": ["Highpass", 0.000000, 0.000000, 1.000000],
                "HPfreq": ["Highpass Frequency", 20.000000, 5.000000, 1250.000000],
                "HPQ": ["HighPass Resonance", 0.700000, 0.000000, 1.400000],
                "LowPass": ["Lowpass", 0.000000, 0.000000, 1.000000],
                "LPfreq": ["Lowpass Frequency", 20000.000000, 500.000000, 20000.000000],
                "LPQ": ["LowPass Resonance", 1.000000, 0.000000, 1.400000],
                "LSsec": ["Lowshelf", 1.000000, 0.000000, 1.000000],
                "LSfreq": ["Lowshelf Frequency", 80.000000, 25.000000, 400.000000],
                "LSq": ["Lowshelf Bandwidth", 1.000000, 0.062500, 4.000000],
                "LSgain": ["Lowshelf Gain", 0.000000, -18.000000, 18.000000],
                "sec1": ["Section 1", 1.000000, 0.000000, 1.000000],
                "freq1": ["Frequency 1", 160.000000, 20.000000, 2000.000000],
                "q1": ["Bandwidth 1", 0.600000, 0.062500, 4.000000],
                "gain1": ["Gain 1", 0.000000, -18.000000, 18.000000],
                "sec2": ["Section 2", 1.000000, 0.000000, 1.000000],
                "freq2": ["Frequency 2", 397.000000, 40.000000, 4000.000000],
                "q2": ["Bandwidth 2", 0.600000, 0.062500, 4.000000],
                "gain2": ["Gain 2", 0.000000, -18.000000, 18.000000],
                "sec3": ["Section 3", 1.000000, 0.000000, 1.000000],
                "freq3": ["Frequency 3", 1250.000000, 100.000000, 10000.000000],
                "q3": ["Bandwidth 3", 0.600000, 0.062500, 4.000000],
                "gain3": ["Gain 3", 0.000000, -18.000000, 18.000000],
                "sec4": ["Section 4", 1.000000, 0.000000, 1.000000],
                "freq4": ["Frequency 4", 2500.000000, 200.000000, 20000.000000],
                "q4": ["Bandwidth 4", 0.600000, 0.062500, 4.000000],
                "gain4": ["Gain 4", 0.000000, -18.000000, 18.000000],
                "HSsec": ["Highshelf", 1.000000, 0.000000, 1.000000],
                "HSfreq": ["Highshelf Frequency", 8000.000000, 1000.000000, 16000.000000],
                "HSq": ["Highshelf Bandwidth", 1.000000, 0.062500, 4.000000],
                "HSgain": ["Highshelf Gain", 0.000000, -18.000000, 18.000000]}
            }
    }

def clamp(v, min_value, max_value):
    return max(min(v, max_value), min_value)

class PolyValue(QObject):
    # name, min, max, value
    def __init__(self, startname="", startval=0, startmin=0, startmax=1, curve_type="lin"):
        QObject.__init__(self)
        self.nameval = startname
        self.valueval = startval
        self.rminval = startmin
        self.rmax = startmax
        self.assigned_cc = None

    def readValue(self):
        return self.valueval

    def setValue(self,val):
        # clamp values
        self.valueval = clamp(val, self.rmin, self.rmax)
        self.value_changed.emit()
        # print("setting value", val)

    @Signal
    def value_changed(self):
        pass

    value = Property(float, readValue, setValue, notify=value_changed)

    def readName(self):
        return self.nameval

    def setName(self,val):
        self.nameval = val
        self.name_changed.emit()

    @Signal
    def name_changed(self):
        pass

    name = Property(str, readName, setName, notify=name_changed)

    def readRMin(self):
        return self.rminval

    def setRMin(self,val):
        self.rminval = val
        self.rmin_changed.emit()

    @Signal
    def rmin_changed(self):
        pass

    rmin = Property(float, readRMin, setRMin, notify=rmin_changed)

    def readRMax(self):
        return self.rmaxval

    def setRMax(self,val):
        self.rmaxval = val
        self.rmax_changed.emit()

    @Signal
    def rmax_changed(self):
        pass

    rmax = Property(float, readRMax, setRMax, notify=rmax_changed)

effect_parameter_data = {
        "reverb": {"gain": PolyValue("gain", 0, -90, 24), "ir": PolyValue("/audio/reverbs/emt_140_dark_1.wav", 0, 0, 1),
            "carla_level": PolyValue("level", 1, 0, 1)},
        "postreverb": {"routing": PolyValue("gain", 6, 0, 6), "carla_level": PolyValue("level", 1, 0, 1)},
        "cab": {"gain": PolyValue("gain", 0, -90, 24), "ir": PolyValue("/audio/cabs/1x12cab.wav", 0, 0, 1),
            "carla_level": PolyValue("level", 1, 0, 1)},
        "postcab": {"gain": PolyValue("gain", 0, -90, 24), "carla_level": PolyValue("level", 1, 0, 1)},
        # "lfo1": lfos[0],
        # "lfo2": lfos[1],
        # "lfo3": lfos[2],
        # "lfo4": lfos[3],
        "mclk": {"carla_level": PolyValue("level", 1, 0, 1)},
}

selected_effect_ports = QStringListModel()
selected_effect_ports.setStringList(["val1", "val2"])
seq_num = 10


def from_backend_new_effect(effect_name, effect_type, x=20, y=30):
    # called by engine code when new effect is created
    # add effect_parameter_data for all parameters / ports
    # print("from backend new effect", effect_name, effect_type)
    if patch_bay_model.patch_bay_singleton is not None:
        patch_bay_model.patch_bay_singleton.startInsert()

    current_effects[effect_name] = {"x": x, "y": y, "effect_type": effect_type,
            "controls": {k : PolyValue(*v) for k,v in effect_prototypes[effect_type]["controls"].items()},
            "highlight": False}
    if patch_bay_model.patch_bay_singleton is not None:
        patch_bay_model.patch_bay_singleton.endInsert()
    # insert in context or model? 
    context.setContextProperty("currentEffects", current_effects) # might be slow


def from_backend_remove_effect(effect_name):
    # called by engine code when effect is removed
    if patch_bay_model.patch_bay_singleton is not None:
        patch_bay_model.patch_bay_singleton.startRemove(effect_name)
    current_effects.pop(effect_name)
    if patch_bay_model.patch_bay_singleton is not None:
        patch_bay_model.patch_bay_singleton.endRemove()

def generate_current_arcs():
    # return x,y pairs for each arc and colour
    # for source in port_connections:
    #     a.
    pass

class Knobs(QObject):
    @Slot(bool, str, str)
    def set_current_port(self, is_source, effect_id, port_name):
        print("port name is", port_name)
        # if source highlight targets
        if is_source:
            # set current source port
            # effect_id, port_name
            # highlight effects given source port
            global current_source_port
            current_source_port = "/".join((effect_id, port_name))
            for id, effect in current_effects.items():
                effect["highlight"] = False
                if id != effect_id:
                    for input_port, style in effect_prototypes[effect["effect_type"]]["inputs"].items():
                        if style == effect_prototypes[current_effects[effect_id]["effect_type"]]["outputs"][port_name]:
                            # highlight and break
                            effect["highlight"] = True
                            break
        else:
            # if target disable highlight
            for id, effect in current_effects.items():
                effect["highlight"] = False
            # add connection between source and target
            # or just wait until it's automatically created from engine? 
            if current_source_port not in port_connections:
                port_connections[current_source_port] = []
            if [effect_id, port_name] not in port_connections[current_source_port]:
                port_connections[current_source_port].append([effect_id, port_name])


            s_effect, s_port = current_source_port.split("/")
            s_effect_type = current_effects[s_effect]["effect_type"]
            t_effect_type = current_effects[effect_id]["effect_type"]
            if t_effect_type == "output" or t_effect_type == "input":
                if s_effect_type == "output" or s_effect_type == "input":
                    ingen_wrapper.connect_port("/main/"+s_effect, "/main/"+effect_id)
                else:
                    ingen_wrapper.connect_port("/main/"+current_source_port, "/main/"+effect_id)
            else:
                if s_effect_type == "output" or s_effect_type == "input":
                    ingen_wrapper.connect_port("/main/"+s_effect, "/main/"+effect_id+"/"+port_name)
                else:
                    ingen_wrapper.connect_port("/main/"+current_source_port, "/main/"+effect_id+"/"+port_name)


            # if [effect_id, port_name] not in inv_port_connections:
            #     inv_port_connections[[effect_id, port_name]] = []
            # if current_source_port not in inv_port_connections[[effect_id, port_name]]:
            #     inv_port_connections[[effect_id, port_name]].append(current_source_port)

            print("port_connections is", port_connections)
            # global context
            context.setContextProperty("portConnections", port_connections)


    @Slot(bool, str)
    def select_effect(self, is_source, effect_id):
        effect_type = current_effects[effect_id]["effect_type"]
        print("selecting effect type", effect_type)
        if is_source:
            selected_effect_ports.setStringList(list(effect_prototypes[effect_type]["outputs"].keys()))
        else:
            selected_effect_ports.setStringList(list(effect_prototypes[effect_type]["inputs"].keys()))

    @Slot(str)
    def list_connected(self, effect_id):
        ports = []
        for source_port, connected in port_connections.items():
            s_effect, s_port = source_port.split("/")
            # connections where we are target
            for c_effect, c_port in connected:
                if c_effect == effect_id or s_effect == effect_id:
                    ports.append(s_effect+"/"+s_port+"---"+c_effect+"/"+c_port)
        print("connected ports:", ports)
        selected_effect_ports.setStringList(ports)

    @Slot(str)
    def disconnect_port(self, port_pair):
        source_pair, target_pair = port_pair.split("---")
        t_effect, t_port = target_pair.split("/")
        port_connections[source_pair].pop(port_connections[source_pair].index([t_effect, t_port]))
        context.setContextProperty("portConnections", port_connections)
        ingen_wrapper.disconnect_port("/main/"+source_pair, "/main/"+target_pair)

        s_effect, s_port = source_pair.split("/")
        s_effect_type = current_effects[s_effect]["effect_type"]
        t_effect_type = current_effects[t_effect]["effect_type"]
        if t_effect_type == "output" or t_effect_type == "input":
            if s_effect_type == "output" or s_effect_type == "input":
                ingen_wrapper.disconnect_port("/main/"+s_effect, "/main/"+t_effect)
            else:
                ingen_wrapper.disconnect_port("/main/"+source_pair, "/main/"+t_effect)
        else:
            if s_effect_type == "output" or s_effect_type == "input":
                ingen_wrapper.disconnect_port("/main/"+s_effect, "/main/"+target_pair)
            else:
                ingen_wrapper.disconnect_port("/main/"+source_pair, "/main/"+target_pair)

    @Slot(str)
    def add_new_effect(self, effect_type):
        # calls backend to add effect
        # TODO actually call backend.
        global seq_num
        seq_num = seq_num + 1
        print("add new effect", effect_type)
        # if there's existing effects of this type, increment the ID
        effect_name = effect_type+str(1)
        for i in range(1, 1000):
            if effect_type+str(i) not in current_effects:
                effect_name = effect_type+str(i)
                break
        ingen_wrapper.add_plugin(effect_name, effect_type_map[effect_type])
        from_backend_new_effect(effect_name, effect_type)


    @Slot(str, int, int)
    def move_effect(self, effect_name, x, y):
        current_effects[effect_name]["x"] = x
        current_effects[effect_name]["y"] = y

    @Slot(str)
    def remove_effect(self, effect_id):
        # calls backend to remove effect
        # TODO actually call backend.
        print("remove effect", effect_id)
        ingen_wrapper.remove_plugin("/main/"+effect_id)
        from_backend_remove_effect(effect_id)

    @Slot(str, str, 'double')
    def ui_knob_change(self, effect_name, parameter, value):
        # print(x, y, z)
        if (effect_name in current_effects) and (parameter in current_effects[effect_name]["controls"]):
            current_effects[effect_name]["controls"][parameter].value = value
            # send_core_message("knob_change", (effect_name, parameter, value))
            ingen_wrapper.set_parameter_value("/main/"+effect_name+"/"+parameter, value)
        else:
            print("effect not found")

    @Slot(str, str)
    def update_ir(self, effect_id, ir_file):
        is_cab = True
        effect_type = current_effects[effect_id]["effect_type"]
        if effect_type in ["mono_reverb", "stereo_reverb", "true_stereo_reverb"]:
            is_cab = False
        ingen_wrapper.set_file(effect_id, ir_file, is_cab)

def add_io():
    for i in range(1,5):
        ingen_wrapper.add_input("input"+str(i))
        from_backend_new_effect("input"+str(i), "input", x=800, y=(80 * i))

    for i in range(1,5):
        ingen_wrapper.add_output("output"+str(i))
        from_backend_new_effect("output"+str(i), "output", x=50, y=(80 * i))

#     @Slot(str)
#     def ui_add_connection(self, x):
#         i = model.stringList().index(x)
#         model.removeRows(i, 1)
#         j = len(model2.stringList())
#         model2.insertRows(j, 1)
#         model2.setData(model2.index(j), x)
#         print(x)

#     @Slot(str)
#     def ui_remove_connection(self, x):
#         i = model.stringList().index(x)
#         model.removeRows(i, 1)
#         print(x)

#     @Slot(str)
#     def toggle_enabled(self, x):
#         print(x)


# class PolyValue(QObject):
#     # name, min, max, value
#     def __init__(self, startname="", startval=0, startmin=0, startmax=1, curve_type="lin"):
#         QObject.__init__(self)
#         self.nameval = startname
#         self.valueval = startval
#         self.rminval = startmin
#         self.rmax = startmax

#     def readValue(self):
#         return self.valueval

#     def setValue(self,val):
#         self.valueval = val
#         self.value_changed.emit()
#         print("setting value", val)

#     @Signal
#     def value_changed(self):
#         pass

#     value = Property(int, readValue, setValue, notify=value_changed)

#     def readName(self):
#         return self.nameval

#     def setName(self,val):
#         self.nameval = val
#         self.name_changed.emit()

#     @Signal
#     def name_changed(self):
#         pass

#     name = Property(str, readName, setName, notify=name_changed)

#     def readRMin(self):
#         return self.rminval

#     def setRMin(self,val):
#         self.rminval = val
#         self.rmin_changed.emit()

#     @Signal
#     def rmin_changed(self):
#         pass

#     rmin = Property(int, readRMin, setRMin, notify=rmin_changed)

#     def readRMax(self):
#         return self.rmaxval

#     def setRMax(self,val):
#         self.rmaxval = val
#         self.rmax_changed.emit()

#     @Signal
#     def rmax_changed(self):
#         pass

#     rmax = Property(int, readRMax, setRMax, notify=rmax_changed)

# obj = {"delay1": PolyValue()}
# obj["delay1"].value = 47

# print(obj["delay1"].value)

# model = QStringListModel()
# model2 = QStringListModel()

# def tick():
#     print("tick")
#     if obj["delay1"].value < 100:
#         obj["delay1"].value += 1
#     else:
#         obj["delay1"].value = 0

effect_type_map = { "delay": "http://polyeffects.com/lv2/digit_delay",
        "mono_reverb": "http://polyeffects.com/lv2/polyconvo#Mono",
        "stereo_reverb": "http://polyeffects.com/lv2/polyconvo#MonoToStereo",
        "true_stereo_reverb": "http://polyeffects.com/lv2/polyconvo#Stereo",
        "mono_cab": "http://gareus.org/oss/lv2/convoLV2#Mono",
        "stereo_cab": "http://gareus.org/oss/lv2/convoLV2#MonoToStereo",
        "true_stereo_cab": "http://gareus.org/oss/lv2/convoLV2#Stereo",
        "mixer": "http://gareus.org/oss/lv2/matrixmixer#i4o4",
        "warmth": "http://moddevices.com/plugins/tap/tubewarmth",
        "reverse": "http://moddevices.com/plugins/tap/reflector",
        "saturator": "http://moddevices.com/plugins/tap/sigmoid",
        "mono_EQ": "http://gareus.org/oss/lv2/fil4#mono",
        "stereo_EQ": "http://gareus.org/oss/lv2/fil4#stereo",
        "filter": "http://drobilla.net/plugins/fomp/mvclpf1",
        "lfo": "http://polyeffects.com/lv2/polylfo"}

if __name__ == "__main__":

    app = QGuiApplication(sys.argv)
    QIcon.setThemeName("digit")
    # Instantiate the Python object.
    knobs = Knobs()

    # t_list = QStringList()
    # t_list.append("a")
    # t_list.append("b")
    # t_list.append("c")
    # model.setStringList(["aasdfasdf", "b", "c"])
    # model2.setStringList(["fff", "ddd" "c"])
    update_counter = PolyValue("update counter", 0, 0, 500000)

    available_effects = QStringListModel()
    available_effects.setStringList(list(effect_type_map.keys()))
    engine = QQmlApplicationEngine()

    qmlRegisterType(patch_bay_model.PatchBayModel, 'Poly', 1, 0, 'PatchBayModel')
    # Expose the object to QML.
    # global context
    context = engine.rootContext()
    context.setContextProperty("knobs", knobs)
    # context.setContextProperty("param_vals", obj)
    # context.setContextProperty("delay1_Left_Out_AvailablePorts", model)
    context.setContextProperty("available_effects", available_effects)
    context.setContextProperty("selectedEffectPorts", selected_effect_ports)
    context.setContextProperty("portConnections", port_connections)
    context.setContextProperty("effectPrototypes", effect_prototypes)
    context.setContextProperty("updateCounter", update_counter)
    # engine.load(QUrl("qrc:/qml/digit.qml"))
    # from_backend_new_effect("delay1", "delay", 20, 30);
    # from_backend_new_effect("delay2", "delay", 250, 290);
    add_io()
    engine.load(QUrl("qml/TestWrapper.qml"))

    # timer = QTimer()
    # timer.timeout.connect(tick)
    # timer.start(1000)

    app.exec_()
