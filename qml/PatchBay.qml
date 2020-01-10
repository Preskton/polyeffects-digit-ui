import QtQuick 2.4
import QtQuick.Window 2.2
import QtQuick.Controls 2.3
import QtQuick.Controls.Material 2.3

import Poly 1.0
import "polyconst.js" as Constants
/*
 * connection pairs of id / port, id / port
 *
 */

    Item {
        x: 0
        y: 0
        id: patch_bay
        width: 1280
        height: 548

        enum PatchMode {
            Select,
            Move,
            Connect,
            Sliders,
            Details
        }
        property int active_width: 900
        property int updateCount: updateCounter, externalRefresh()
        property int current_index: -1
        property bool isMoving: false
        property int currentMode: PatchBay.Select
        // relate to port selection popup
        property bool list_source: true
        property string list_effect_id
        property var effect_map: {"invalid":"b"}
        property PatchBayEffect selected_effect

		function setColorAlpha(color, alpha) {
			return Qt.hsla(color.hslHue, color.hslSaturation, color.hslLightness, alpha)
		}

        function externalRefresh() {
            mycanvas.requestPaint();
            return updateCounter.value;
        }

        Component.onCompleted: {
            title_footer.patch_single = patch_bay;
        }

        function rsplit(str, sep, maxsplit) {
            var split = str.split(sep);
            return maxsplit ? [ split.slice(0, -maxsplit).join(sep) ].concat(split.slice(-maxsplit)) : split;
        }
        // Column {
        //     x: 0
        //     y: 0
        //     z:2
        //     Rectangle {
        //         x: 0
        //         y: 0
        //         color: accent_color
        //         width: 58
        //         height: 36
        //         border { width:1; color: "white"}

        //         Label {
        //             // color: "#ffffff"
        //             text: "out"
        //             elide: Text.ElideRight
        //             anchors.centerIn: parent
        //             horizontalAlignment: Text.AlignHCenter
        //             // width: 1000
        //             // height: 60
        //             // z: 3
        //             color: "white"
        //             font {
        //                 pixelSize: 22
        //                 capitalization: Font.AllUppercase
        //             }
        //         }
        //     }
        //     IOPort {
        //         io_num: 1
        //         port_name: "output1"
        //         effect_type: "output"
        //     }
        //     IOPort {
        //         io_num: 2
        //         port_name: "output2"
        //         effect_type: "output"
        //     }
        //     IOPort {
        //         io_num: 3
        //         port_name: "output3"
        //         effect_type: "output"
        //     }
        //     IOPort {
        //         io_num: 4
        //         port_name: "output4"
        //         effect_type: "output"
        //     }
        // }

        // Column {
        //     x: 1222 
        //     y: 0
        //     z:2
        //     Rectangle {
        //         x: 0
        //         y: 0
        //         color: accent_color
        //         width: 58
        //         height: 36
        //         border { width:1; color: "white"}

        //         Label {
        //             // color: "#ffffff"
        //             text: "in"
        //             elide: Text.ElideRight
        //             anchors.centerIn: parent
        //             horizontalAlignment: Text.AlignHCenter
        //             // width: 1000
        //             // height: 60
        //             // z: 3
        //             color: "white"
        //             font {
        //                 pixelSize: 22
        //                 capitalization: Font.AllUppercase
        //             }
        //         }
        //     }
        //     IOPort {
        //         io_num: 1
        //         port_name: "input1"
        //         effect_type: "input"
        //     }
        //     IOPort {
        //         io_num: 2
        //         port_name: "input2"
        //         effect_type: "input"
        //     }
        //     IOPort {
        //         io_num: 3
        //         port_name: "input3"
        //         effect_type: "input"
        //     }
        //     IOPort {
        //         io_num: 4
        //         port_name: "input4"
        //         effect_type: "input"
        //     }
        // }

        Item {
            x: 0
            width: 1280
            height: parent.height

            Repeater {
                id: rep1
                // model: [1, 2, 3, 4]
                model: PatchBayModel {}
                PatchBayEffect {
                    effect_id: l_effect_id
                    effect_type: l_effect_type
                    x: cur_x
                    y: cur_y
                    highlight: l_highlight
                }
                onItemAdded: {
                    if ("invalid" in effect_map){
                        delete effect_map["invalid"];
                    }
                    // console.log("added", index, item.effect_id);
                    effect_map[item.effect_id] = item;
                    if (!selected_effect){
                        selected_effect = item;
                    }
                    // console.log(Object.keys(effect_map)); //[item.effect_id]);
                }
            }

            Canvas {
                id: mycanvas
                function findConnections(drawContext){ 
                    // iterate over items in rep1, adding to dictionary of effect_id : patchbayeffect
                    // source and targets are the wrong way round XXX 
                    // console.log("finding connection", Object.keys(portConnections));
                    for (var source_effect_port_str in portConnections){ 
                        // console.log("key ", source_effect_port_str);
                        var source_effect_port = rsplit(source_effect_port_str, "/", 1);
                        var targets = portConnections[source_effect_port_str];
                        // console.log("drawing connection 1", source_effect_port[0], portConnections[source_effect_port_str]);
                        
                        for (var target in targets){
                            // console.log("drawing connection 2 targets", targets[0][0]);
                            // console.log("drawing connection 2 obj", effect_map[source_effect_port[0]], effect_map[targets[target][0]]);
                            // console.log("drawing connection 2 keys", source_effect_port[0], targets[target][0]);
                            var target_port_type = effectPrototypes[currentEffects[targets[target][0]]["effect_type"]]["outputs"][targets[target][1]][1]
                            // console.log("target_port_type", target_port_type);
                            //effect_map[source_effect_port[0]], effect_map[targets[target][0]]
                            drawConnection(drawContext, effect_map[source_effect_port[0]], effect_map[targets[target][0]], target_port_type);
                        } 
                    }
                }

                function drawConnection( drawContext, targetPort, sourcePort, source_port_type ) {
                    if (source_port_type == "AudioPort"){
                        var start   = getCanvasCoordinates( targetPort.inputs, 0, 4)
                    } else {
                        var start   = getCanvasCoordinates( targetPort.cv_area, targetPort.cv_area.width / 2, targetPort.cv_area.height - 2)
                    }
                    var end     = getCanvasCoordinates( sourcePort.outputs,  0, 4) 
                    if( start.x > end.x ) {
                        var tmp = start;
                        start = end;
                        end = tmp;
                    }

                    var minmax  = getMinMax( start, end )
                    var sizeX   = minmax[2] - minmax[0]


                    drawContext.lineWidth   = 2;
                    var line_color;  
                    if (source_port_type == "CVPort"){
                        line_color = Constants.cv_color;
                    } 
                    else if (source_port_type == "AudioPort"){
                        line_color = Constants.audio_color;
                    }
                    else if (source_port_type == "ControlPort"){
                        line_color = Constants.control_color;
                    } else {
                        line_color = accent_color;
                    }

                    if (patch_bay.isMoving){
                        drawContext.strokeStyle = Constants.outline_color;
                    } else {
                        drawContext.strokeStyle = line_color;
                    }
                    drawContext.beginPath();
                    drawContext.moveTo( start.x, start.y );
                    if (source_port_type == "AudioPort"){
                        drawContext.bezierCurveTo( start.x + sizeX / 2.0 , start.y, end.x - sizeX / 2.0, end.y, end.x, end.y );
                    } else {
                        drawContext.bezierCurveTo( start.x, start.y + 50, end.x - sizeX / 2, end.y, end.x, end.y );
                    }
                    drawContext.stroke();
                    return true;
                }

                function getCanvasCoordinates( port, hotSpotX, hotSpotY )
                {
                    return mycanvas.mapFromItem( port, hotSpotX, hotSpotY )
                }

                function getMinMax( start, end )
                {
                    var minX, minY,
                    maxX, maxY
                    if( start.x < end.x ) {
                        minX = start.x
                        maxX = end.x
                    }
                    else {
                        minX = end.x
                        maxX = start.x
                    }

                    if( start.y < end.y ) {
                        minY = start.y
                        maxY = end.y
                    }
                    else {
                        minY = end.y
                        maxY = start.y
                    }
                    return [minX, minY, maxX, maxY]
                }

                anchors {
                    top: parent.top
                    right:  parent.right
                    bottom:  parent.bottom
                }
                width: parent.width
                onPaint: {
                    var ctx = getContext("2d");
                    ctx.fillStyle = Material.background; //Qt.rgba(1, 1, 0, 1);
                    ctx.fillRect(0, 0, width, height);
                    findConnections(ctx);
                }
                DropArea {
                    anchors.fill: parent
                    onEntered: drag.source.caught = true;
                    onExited: drag.source.caught = false;
                }
            }

            Rectangle {
                z: 3
                id: darken_patch
                anchors.fill: parent
                color: "#90000000"
                visible: patch_bay.currentMode == PatchBay.Sliders
                MouseArea {
                    anchors.fill: parent
                    onClicked: {}
                }
            }

            // bottom buttons
            // normal
            // add
            // remove
            // move
            //

            Column {
                visible: patch_bay.currentMode == PatchBay.Sliders
                y: 67
                x: 1043
                id: action_icons
                z: 6
                spacing: 25
                IconButton {
                    icon.name: "connect"
                    visible: selected_effect && (selected_effect.effect_type != "output")
                    width: 60
                    height: 60
                    onClicked: {
                        selected_effect.connect_clicked();
                        currentMode = PatchBay.Connect;
                    }
                    Material.background: "white"
                    Material.foreground: accent_color
                    radius: 28

                    Label {
                        visible: title_footer.show_help 
                        x: -92
                        y: 19 
                        text: "connect"
                        horizontalAlignment: Text.AlignRight
                        width: 82
                        height: 9
                        z: 1
                        color: "white"
                        font {
                            pixelSize: 14
                            capitalization: Font.AllUppercase
                        }
                    }
                }
                IconButton {
                    id: disconnectMode
                    icon.name: "disconnect"
                    width: 60
                    height: 60
                    onClicked: {
                        selected_effect.disconnect_clicked()
                    }
                    Material.background: "white"
                    Material.foreground: accent_color
                    radius: 28

                    Label {
                        visible: title_footer.show_help 
                        x: -92
                        y: 19 
                        text: "disconnect"
                        horizontalAlignment: Text.AlignRight
                        width: 82
                        height: 9
                        z: 1
                        color: "white"
                        font {
                            pixelSize: 14
                            capitalization: Font.AllUppercase
                        }
                    }
                }
                IconButton {
                    icon.name: "move"
                    width: 60
                    height: 60
                    onClicked: {
                        currentMode = PatchBay.Move;
                        selected_effect.hide_sliders(false);
                    }
                    Material.background: "white"
                    Material.foreground: accent_color
                    radius: 28
                    Label {
                        visible: title_footer.show_help 
                        x: -92
                        y: 19 
                        text: "move"
                        horizontalAlignment: Text.AlignRight
                        width: 82
                        height: 9
                        z: 1
                        color: "white"
                        font {
                            pixelSize: 14
                            capitalization: Font.AllUppercase
                        }
                    }
                }
                IconButton {
                    id: expandMode
                    visible: selected_effect && (selected_effect.has_ui)
                    icon.name: "view"
                    width: 60
                    height: 60
                    onClicked: {
                        selected_effect.hide_sliders(false);
                        selected_effect.expand_clicked();
                    }
                    Material.background: "white"
                    Material.foreground: accent_color
                    radius: 28
                    Label {
                        visible: title_footer.show_help 
                        x: -92
                        y: 19 
                        text: "main controls"
                        horizontalAlignment: Text.AlignRight
                        width: 82
                        height: 9
                        z: 1
                        color: "white"
                        font {
                            pixelSize: 14
                            capitalization: Font.AllUppercase
                        }
                    }
                }
                // IconButton {
                //     id: helpMode
                //     icon.name: "help"
                //     width: 56
                //     height: 56
                //     onClicked: {
                //         console.log("clicked:");
                //     }
                //     Material.background: "white"
                //     Material.foreground: accent_color
                //     radius: 28
                // }
                IconButton {
                    visible: selected_effect && (selected_effect.effect_type != "input" && selected_effect.effect_type != "output")
                    id: deleteMode
                    icon.name: "delete"
                    width: 60
                    height: 60
                    onClicked: {
                        selected_effect.delete_clicked()
                    }
                    Material.background: "white"
                    Material.foreground: accent_color
                    radius: 28
                    Label {
                        visible: title_footer.show_help 
                        x: -92
                        y: 19 
                        text: "delete"
                        horizontalAlignment: Text.AlignRight
                        width: 82
                        height: 9
                        z: 1
                        color: "white"
                        font {
                            pixelSize: 14
                            capitalization: Font.AllUppercase
                        }
                    }
                }
            }
        }


        Component {
            id: portSelection
            Item {
                id: portSelectionCon
                y: 50
                height:700
                width:1280

                GlowingLabel {
                    color: "#ffffff"
                    text: "Choose Port"
                    font {
                        pixelSize: fontSizeLarge * 1.2
                    }
                    anchors.top: parent.top
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                ListView {
                    width: 400
                    spacing: 5
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 90
                    anchors.bottom: parent.bottom
                    clip: true
                    delegate: ItemDelegate {
                        width: parent.width
                        height: 90
                        text: edit.split("|")[1]
                        bottomPadding: 2
                        font.pixelSize: fontSizeLarge
                        topPadding: 2
                        onClicked: {
                            // set this as the current port
                            // and update valid targets
                            knobs.set_current_port(list_source, list_effect_id, edit.split("|")[0]);
                            rep1.model.items_changed();
                            mycanvas.requestPaint();
                            mainStack.pop();
                        }
                    }
                    ScrollIndicator.vertical: ScrollIndicator {
                        anchors.top: parent.top
                        parent: portSelectionCon
                        anchors.right: parent.right
                        anchors.rightMargin: 1
                        anchors.bottom: parent.bottom
                    }
                    model: selectedEffectPorts
                }
            
                
                IconButton {
                    x: 34 
                    y: 596
                    icon.width: 15
                    icon.height: 25
                    width: 119
                    height: 62
                    text: "BACK"
                    font {
                        pixelSize: 24
                    }
                    flat: false
                    icon.name: "back"
                    Material.background: "white"
                    Material.foreground: Constants.outline_color
                    HelpLabel {
                        text: "back"
                    }

                    onClicked: mainStack.pop()
                }
            }
        }

        Component {
            id: disconnectPortSelection
            Item {
                id: disPortSelectionCon
                y: 50
                height:700
                width:1280

                GlowingLabel {
                    color: "#ffffff"
                    text: "Disconnect Port"
                    font {
                        pixelSize: fontSizeLarge * 1.2
                    }
                    anchors.top: parent.top
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                ListView {
                    width: 400
                    spacing: 5
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 90
                    anchors.bottom: parent.bottom
                    clip: true
                    delegate: ItemDelegate {
                        width: parent.width
                        height: 90
                        text: edit
                        bottomPadding: 2
                        font.pixelSize: fontSizeLarge
                        topPadding: 2
                        onClicked: {
                            // set this as the current port
                            // and update valid targets
                            //knobs.set_current_port(list_source, list_effect_id, edit);
                            // console.log("disconnect", edit);
                            knobs.disconnect_port(edit);
                            mycanvas.requestPaint();
                            // rep1.model.add_effect(edit)
                            // knobs.ui_add_effect(edit)
                            mainStack.pop();
                        }
                    }
                    ScrollIndicator.vertical: ScrollIndicator {
                        anchors.top: parent.top
                        parent: disPortSelectionCon
                        anchors.right: parent.right
                        anchors.rightMargin: 1
                        anchors.bottom: parent.bottom
                    }
                    model: selectedEffectPorts
                }
            
                
                IconButton {
                    x: 34 
                    y: 596
                    icon.width: 15
                    icon.height: 25
                    width: 119
                    height: 62
                    text: "BACK"
                    font {
                        pixelSize: 24
                    }
                    flat: false
                    icon.name: "back"
                    Material.background: "white"
                    Material.foreground: Constants.outline_color
                    HelpLabel {
                        text: "back"
                    }

                    onClicked: mainStack.pop()
                }

            }
        }

        // Popup {
        //     id: portSelectionPopup
        //     property var ports: []
        //     // x: 500
        //     // y: 200
        //     width: 600
        //     height: 400
        //     modal: true
        //     focus: true
        //     closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        //     parent: Overlay.overlay
        //     Overlay.modal: Rectangle {
        //         // x: 500
        //         // y: -560
        //         width: 1280
        //         height: 1280
        //         color: "#AA333333"
        //         transform: Rotation {
        //             angle: -90
        //             // origin.x: Screen.height / 2
        //             // origin.x: Screen.height / 2
        //             // origin.x: 720 / 2
        //             // origin.y: 720 / 2
        //             origin.x: 1280 / 2
        //             origin.y: 1280 / 2
        //         }
        //     }

        //     x: Math.round((parent.width - width) / 2)
        //     y: Math.round((parent.height - height) / 2)

        //     function open_port_selection(effect){
        //         portSelectionPopup.open()
        //     }

        //     Item {
        //         id: portSelectCont
        //         anchors.centerIn: parent
        //         width:500
        //         height:500
        //         Label {
        //             text: "Select Port"
        //             font.pixelSize: baseFontSize
        //             width: 190
        //         }
        //         ListView {
        //             width: 400
        //             anchors.centerIn: parent
        //             clip: true
        //             delegate: ItemDelegate {
        //                 width: parent.width
        //                 height: 50
        //                 text: edit
        //                 bottomPadding: 0
        //                 font.pixelSize: fontSizeMedium
        //                 topPadding: 0
        //                 onClicked: {
        //                     // rep1.model.add_effect(edit)
        //                     // knobs.ui_add_effect(edit)
        //                     // mainStack.pop()
        //                     portSelectionPopup.close()
        //                 }
        //             }
        //             ScrollIndicator.vertical: ScrollIndicator {
        //                 anchors.top: parent.top
        //                 parent: portSelectCont
        //                 anchors.right: parent.right
        //                 anchors.rightMargin: 1
        //                 anchors.bottom: parent.bottom
        //             }
        //             model: selectedEffectPorts
        //         }
        //     }
        // } 
    }
