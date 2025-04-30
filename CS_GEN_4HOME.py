import os

"""
These are variables the User needs to set:
"""
BASE_DIR = r"C:\Users\tyler\Desktop\py4e\AFX_Contact_Sheet\Tracker_Premier_Music_Store_20"
FRAME_NUMBER = "0318"  # Define frame number as a variable for easy modification
IMG_NAME = "my_contact_sheet" # Replace with your own name
IMG_EXT = ".jpg" # Change if desired
IMG_TYPE = "jpeg" # Change if desired
NUKE_NON_COMMERCIAL = True # Set to True if using NC. Else, False

"""
No need to touch anything beyond this.
Main Program Begins...
"""

def main():

    print("Starting Program...\n\n")

    # List to store all latest EXR file paths
    latest_exr_files = []

    print("\nChecking for updates...")  # Indicate the script is running

    # Get list of shot folders (folders named with numbers)
    shot_folders = [item for item in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, item)) and item.isdigit()]

    for shot in shot_folders:
        shot_seq_folders_path = os.path.join(BASE_DIR, shot, "RENDERS", "comp")
        if not os.path.exists(shot_seq_folders_path):
            continue  

        latest_folder_version = "00"
        latest_seq_folder = None

        # Find the latest sequence folder
        for seq_folder in os.listdir(shot_seq_folders_path):
            if "_v" in seq_folder:
                parts = seq_folder.split("_v")
                if len(parts) > 1 and parts[1].isdigit():
                    version = int(parts[1])
                    formatted_version = "{:02}".format(version)

                    if version > int(latest_folder_version):
                        latest_folder_version = formatted_version
                        latest_seq_folder = seq_folder

        if latest_seq_folder:
            seq_folder_path = os.path.join(shot_seq_folders_path, latest_seq_folder)
            exr_file = shot + "_COMP_v" + latest_folder_version + "." + FRAME_NUMBER + ".exr"
            exr_path = os.path.join(seq_folder_path, exr_file)

            if os.path.isfile(exr_path):
                latest_exr_files.append(exr_path)  # Add to the list

    # Print results
    print("\nLatest EXR files detected:")
    for file in latest_exr_files:
        print(file)

    # Return the list (for use in other scripts if needed)
    latest_exr_files

    def fix_path(path):
        new_path = path.replace(os.sep, '/')
        return new_path

    # Iterates through file paths, fixes them, and creates Read Nodes for each
    read_node_list = []

    for i in latest_exr_files:
        g = fix_path(i)
        read_node = nuke.nodes.Read(name=g, file=g)
        read_node_list.append(read_node)

    # Creates Text Nodes
    text_node_list = []
    for index, read_node in enumerate(read_node_list):
        text_node = nuke.nodes.Text2()
        text_node["message"].setValue("[file rootname [file tail [value input0.file]]]")
        text_node["yjustify"].setValue("bottom")
        text_node["box"].setValue([13, 13, 13, 13])  # Example values (x, y, right, top)
        text_node["enable_shadows"].setValue("True")    
        text_node["shadow_angle"].setValue(225)
        text_node["shadow_distance"].setValue(8.6)
        text_node["shadow_softness"].setValue(2)
        text_node["shadow_size"].setValue(2.85)
        text_node["shadow_opacity"].setValue(1)
        text_node.setInput(0, read_node)  
        text_node_list.append(text_node)

    # Creates Contact Sheet Node and positions it dynamically
    contact_sheet = nuke.nodes.ContactSheet()
    contact_sheet["width"].setExpression("[value input.width]*columns")
    contact_sheet["height"].setExpression("[value input.height]*rows")
    contact_sheet["roworder"].setValue("TopBottom")
    contact_sheet["rows"].setExpression("[python -execlocal import\\ math\\nret\\ =\\ math.ceil(float(nuke.thisNode().inputs())\\ /\\ max(nuke.thisNode().knob('columns').value(),\\ 1))]")
    contact_sheet["columns"].setExpression("[python -execlocal import\\ math\\nret\\ =\\ math.ceil(math.sqrt(nuke.thisNode().inputs()))]")
    for index, text_node in enumerate(text_node_list):
        contact_sheet.setInput(index, text_node)  

    # Creates a Reformat Node, comment out this block unless using Nuke Non-Commercial
    if NUKE_NON_COMMERCIAL:
        reformat_node = nuke.nodes.Reformat()
        reformat_node["format"].setValue("HD_1080")
        reformat_node["resize"].setValue("fit")
        reformat_node.setInput(0, contact_sheet)
    else:
        print("skipping NC")

    # Creates Write Node
    print("\n\nWriting new contact sheet!")
    write_path = fix_path(os.path.join(BASE_DIR, IMG_NAME + IMG_EXT))
    write_node = nuke.nodes.Write()
    write_node["file_type"].setValue(IMG_TYPE)
    write_node["file"].setValue(write_path)
    if NUKE_NON_COMMERCIAL:
        write_node.setInput(0, reformat_node)
    else:
        write_node.setInput(0, contact_sheet)
    nuke.execute(write_node, int(FRAME_NUMBER), int(FRAME_NUMBER))
    print("\nHere is your contact sheet path: \n" + write_path)
    cs_read = nuke.nodes.Read(file=write_path)
    viewer_node = nuke.createNode("Viewer")
    viewer_node.setInput(0, cs_read)


    # Neatly formats the nodes in the DAG
    def scaleNodes( scale ):
        nodes = nuke.allNodes()    # GET SELECTED NODES
        amount = len( nodes )    # GET NUMBER OF SELECTED NODES
        if amount == 0:    return # DO NOTHING IF NO NODES WERE SELECTED

        allX = sum( [ n.xpos()+n.screenWidth()/2 for n in nodes ] )  # SUM OF ALL X VALUES
        allY = sum( [ n.ypos()+n.screenHeight()/2 for n in nodes ] ) # SUM OF ALL Y VALUES

        # CENTER OF SELECTED NODES
        centreX = allX / amount
        centreY = allY / amount

        # REASSIGN NODE POSITIONS AS A FACTOR OF THEIR DISTANCE TO THE SELECTION CENTER
        for n in nodes:
            n.setXpos( int(centreX + ( n.xpos() - centreX ) * scale ))
            n.setYpos( int(centreY + ( n.ypos() - centreY ) * scale ))
        
    scaleNodes(3)

    # Create a backdrop node behind everything (excluding the Viewer)
    def createBackdrop():
        nodes_to_include = [n for n in nuke.allNodes() if n.Class() != "Viewer"]

        # Get bounds for backdrop placement
        min_x = min(n.xpos() for n in nodes_to_include)
        max_x = max(n.xpos() + n.screenWidth() for n in nodes_to_include)
        min_y = min(n.ypos() for n in nodes_to_include)
        max_y = max(n.ypos() + n.screenHeight() for n in nodes_to_include)

        # Create the backdrop node
        backdrop = nuke.nodes.BackdropNode()
        backdrop["xpos"].setValue(min_x - 50)  # Expand slightly beyond bounds
        backdrop["ypos"].setValue(min_y - 50)
        backdrop["bdwidth"].setValue(max_x - min_x + 100)  # Add padding
        backdrop["bdheight"].setValue(max_y - min_y + 100)
        backdrop["label"].setValue("Contact Sheet")
        backdrop["note_font_size"].setValue(100)  # Sets backdrop text size to 100
        backdrop["tile_color"].setValue(0x5E81ACFF)  # Set a custom color (optional)

    createBackdrop()


    print("\n\nfinished")

if __name__ == "__main__":
    main()