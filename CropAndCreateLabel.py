import xml.etree.ElementTree as ET
import pickle
import os
from os import listdir, getcwd
from os.path import join
import brambox as bb
import numpy as np
from PIL import Image, ImageEnhance,ImageDraw
import brambox as bbb
import shutil
import time
#基础xml文件
baseXmlFile = 'base.xml'

output_dir = 'output'
out_Annotations = output_dir+'/Annotations'
out_labels = output_dir+'/labels'
out_JPEGImages = output_dir+'/JPEGImages'

class AutoCreateXml():
    def __init__(self):
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        if not os.path.exists(out_Annotations):
            os.makedirs(out_Annotations) 
        if not os.path.exists(out_labels):
            os.makedirs(out_labels) 
        if not os.path.exists(out_JPEGImages):
            os.makedirs(out_JPEGImages) 

    def update_xml(self,imageFileName,width,hight,className,boxs):
            outxmlfile = out_Annotations+'/'+imageFileName.split('.')[0]+'.xml'
            if os.path.exists(outxmlfile):
                tree = ET.parse(outxmlfile)
            else:
                tree = ET.parse(baseXmlFile)
            root = tree.getroot()
            for obj in root.iter('filename'):
                obj.text = imageFileName
            for obj in root.iter('folder'):
                obj.text = 'JPEGImages'

            for obj in root.iter('path'):
                obj.text = imageFileName

            for obj in root.iter('size'):
                for width_item in obj.iter('width'):
                        width_item.text = str(width)
                for height_item in obj.iter('height'):
                        height_item.text = str(hight)
            
            #创建obejct其他节点
            newobject = ET.SubElement(root,'object')
            # name node
            name = ET.SubElement(newobject,'name')
            name.text = className
            # pose node
            pose = ET.SubElement(newobject,'pose')
            # truncated node
            truncated = ET.SubElement(newobject,'truncated')
            truncated.text = '0'

            # difficult node
            difficult = ET.SubElement(newobject,'difficult')
            difficult.text = '0'

            # bndbox node
            bndbox = ET.SubElement(newobject,'bndbox')
            ## xmin
            xmin = ET.SubElement(bndbox,'xmin')
            xmin.text = str(boxs[0])
            ## xmin
            ymin = ET.SubElement(bndbox,'ymin')
            ymin.text = str(boxs[1])
            ## xmin
            xmax = ET.SubElement(bndbox,'xmax')
            xmax.text = str(boxs[2])
            ## xmin
            ymax = ET.SubElement(bndbox,'ymax')
            ymax.text = str(boxs[3])
            tree.write(outxmlfile)


class PascalVocAnnotation:
    def __init__(self, id):
        '''
        Args:
            id:file name
        '''
        self.id = id
        self.width = 0
        self.height = 0
        self.annntations = []#{clsname:box}
    def __str__(self):
        return '{},{},{},{}'.format(self.id, self.width, self.height,self.annntations)

class CropAndCreate:
    def __init__(self, voc_label_dir, cls):
        self.voc_label_dir = voc_label_dir
        self.images_label = {}
        self.auto_create_xml = AutoCreateXml()
        self.image_crop_count = 0
        self.starttime = time.strftime('%Y%d%H%M%S',time.localtime(time.time()))
        self.crop_class = cls


    def box_in_person(self, box, person_box):
        return box[0]>person_box[0] and box[0] < person_box[2] \
           and box[1]>person_box[1] and box[1] < person_box[3] \
           and box[2]>person_box[0] and box[2] < person_box[2] \
           and box[3]>person_box[1] and box[3] < person_box[3] \

    def get_crop_image(self, image_path, crop_box):
        '''
        Args:
            crop_box:tuble obejct, content is [left,right,top,bottom]
        '''
        if os.path.exists(image_path):
            image = Image.open(image_path)
            try:
                crop_box_tuple = (crop_box[0], crop_box[1], crop_box[2], crop_box[3])
                img_crop = image.crop(crop_box_tuple)
                return img_crop
            except:
                print("crop {} exception....".format(image_path))
        else:
            print('{image_path} is not exist !')
        return None

    def get_voc_annomation_obejct(self, xml_path):
        '''
        Args:
            xml_path:parscal voc xml file path
        Return:
            PascalVocAnnotation
        '''
        voc_annotation = PascalVocAnnotation(xml_path)
        xml_file = open(xml_path)
        tree=ET.parse(xml_file)
        root = tree.getroot()
        box_info = {}
        # for obj in root.iter('size'):
        #     voc_annotation.width = obj.find('width').txt
        #     voc_annotation.height = obj.find('height').txt
        for obj in root.iter('size'):
            for width_item in obj.iter('width'):
                voc_annotation.width = int(width_item.text)
            for height_item in obj.iter('height'):
                voc_annotation.height = int(height_item.text)
        for obj in root.iter('object'):
            object_item = {}
            cls = obj.find('name').text
            xmlbox = obj.find('bndbox')
            box = (float(xmlbox.find('xmin').text), float(xmlbox.find('ymin').text), float(xmlbox.find('xmax').text), float(xmlbox.find('ymax').text))
            box_info[cls] = box
            object_item['name'] = cls
            object_item['bndbox'] = box
            voc_annotation.annntations.append(object_item)
        return voc_annotation

    def get_randow_file_name(self):
        self.image_crop_count = self.image_crop_count +1;
        return  self.starttime + str(self.image_crop_count).zfill(10)


    def start(self):
        annotations_dir = os.path.join(self.voc_label_dir, 'Annotations')
        images_dir = os.path.join(self.voc_label_dir, 'JPEGImages')
        annotations_files = os.listdir(annotations_dir)
        for xml in annotations_files:
            if xml.endswith('.xml'):
                #get current xml annotation object
                print('parse src {}'.format(xml))
                voc_annotation = self.get_voc_annomation_obejct(os.path.join(annotations_dir,xml))

                for annotation in voc_annotation.annntations:
                    if annotation['name'] == self.crop_class:
                        bbox_person =  annotation['bndbox']
                        image_path = os.path.join(images_dir, xml.split(".xml")[0]+'.jpg')
                        #get crop images
                        crop_image = self.get_crop_image(image_path, bbox_person)
                        next_file_name = self.get_randow_file_name()
                        if crop_image is not None and crop_image.size[0]>0:
                            outfilename =os.path.join(out_JPEGImages, str(next_file_name) + '.jpg')
                            # print(crop_image.size)
                            crop_image.save(outfilename,quality=100)
                            out_xml_name = next_file_name+'.xml'
                            for annotation_other in voc_annotation.annntations:
                                if annotation_other['name'] != self.crop_class:
                                    bbox = annotation_other['bndbox']
                                    if self.box_in_person(bbox, bbox_person):
                                        bbox_inter = []
                                        bbox_inter[:2] = np.array(bbox[:2]) - np.array(bbox_person[:2])
                                        bbox_inter[2:4] = np.array(bbox[2:4]) - np.array(bbox_person[:2])
                                        self.auto_create_xml.update_xml(out_xml_name,crop_image.size[0],crop_image.size[1],annotation_other['name'],bbox_inter)
            shutil.copy(os.path.join(self.voc_label_dir, 'mrconfig.xml'), os.path.join(output_dir, 'mrconfig.xml'))

crop_class = 'person'
src_label_dir = './phone'
crop_and_create = CropAndCreate(src_label_dir, crop_class)
crop_and_create.start()
