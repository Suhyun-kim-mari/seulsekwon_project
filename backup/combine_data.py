
import pandas as pd
import glob
import os
from pyproj import Transformer

def convert_tm_to_wgs84(x, y):
    # EPSG:5181 (Middle Korea Central Belt) to EPSG:4326 (WGS84)
    # Most Seoul retail/shop data from official sources uses 5181 or 5186
    # For X ~ 200,000 and Y ~ 450,000, 5181 is common.
    try:
        transformer = Transformer.from_crs("epsg:5181", "epsg:4326")
        lat, lon = transformer.transform(x, y)
        return lat, lon
    except:
        return None, None

def combine_seoul_data():
    input_dir = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/cleaned'
    output_file = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data.csv'
    
    csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
    
    all_dfs = []
    
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        print(f"Processing {file_name}...")
        
        try:
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='cp949')
            
            normalized_df = pd.DataFrame()
            
            if 'bookstore' in file_name:
                normalized_df['name'] = df['책방 이름']
                normalized_df['address'] = df['주소']
                normalized_df['latitude'] = df['위도']
                normalized_df['longitude'] = df['경도']
                normalized_df['category_large'] = df['카테고리_대']
                normalized_df['category_small'] = df['카테고리_소']
            
            elif 'bus_station' in file_name:
                normalized_df['name'] = df['정류소명']
                normalized_df['address'] = None
                normalized_df['latitude'] = df['경도']
                normalized_df['longitude'] = df['위도']
                normalized_df['category_large'] = df['카테고리_대']
                normalized_df['category_small'] = df['카테고리_소']
                
            elif 'finance' in file_name:
                normalized_df['name'] = df['지점명']
                normalized_df['address'] = df['주소']
                normalized_df['latitude'] = df['위도']
                normalized_df['longitude'] = df['경도']
                normalized_df['category_large'] = df.get('카태고리_대', df.get('카테고리_대'))
                normalized_df['category_small'] = df.get('카태고리_소', df.get('카테고리_소'))
                
            elif 'hospital' in file_name:
                normalized_df['name'] = df['기관명']
                normalized_df['address'] = df['주소']
                normalized_df['latitude'] = df['위도']
                normalized_df['longitude'] = df['경도']
                normalized_df['category_large'] = df['카테고리_대']
                normalized_df['category_small'] = df['카테고리_소']
                
            elif 'large_scale_shop' in file_name:
                normalized_df['name'] = df['사업장명']
                normalized_df['address'] = df['도로명주소']
                
                # Convert TM to WGS84
                lats = []
                lons = []
                # Note: transformer.transform(x, y) might expect (y, x) or (x, y) depending on CRS
                # In 5181, X is Easting, Y is Northing. 
                # transformer.transform(Easting, Northing) -> (Lat, Lon)
                transformer = Transformer.from_crs("epsg:5181", "epsg:4326")
                for x, y in zip(df['좌표정보(X)'], df['좌표정보(Y)']):
                    if pd.notnull(x) and pd.notnull(y):
                        lat, lon = transformer.transform(x, y)
                        lats.append(lat)
                        lons.append(lon)
                    else:
                        lats.append(None)
                        lons.append(None)
                
                normalized_df['latitude'] = lats
                normalized_df['longitude'] = lons
                normalized_df['category_large'] = df['카테고리_대']
                normalized_df['category_small'] = df.get('카태고리_소', df.get('카테고리_소'))
                
            elif 'library' in file_name:
                normalized_df['name'] = df['도서관명']
                normalized_df['address'] = df['주소']
                normalized_df['latitude'] = df['위도']
                normalized_df['longitude'] = df['경도']
                normalized_df['category_large'] = df['카테고리_대']
                normalized_df['category_small'] = df['카테고리_소']
                
            elif 'metro_station' in file_name:
                normalized_df['name'] = df['역명']
                normalized_df['address'] = None
                normalized_df['latitude'] = df['위도']
                normalized_df['longitude'] = df['경도']
                normalized_df['category_large'] = df['카테고리_대']
                normalized_df['category_small'] = df['카테고리_소']
                
            elif 'park' in file_name:
                normalized_df['name'] = df['공원명']
                normalized_df['address'] = df['소재지지번주소']
                normalized_df['latitude'] = df['위도']
                normalized_df['longitude'] = df['경도']
                normalized_df['category_large'] = df['카테고리_대']
                normalized_df['category_small'] = df['카테고리_소']
                
            elif 'police' in file_name:
                normalized_df['name'] = df['관서명']
                normalized_df['address'] = df['주소']
                normalized_df['latitude'] = df['위도']
                normalized_df['longitude'] = df['경도']
                normalized_df['category_large'] = df['카테고리_대']
                normalized_df['category_small'] = df['카테고리_소']
                
            elif 'school' in file_name:
                normalized_df['name'] = df['학교명']
                normalized_df['address'] = df['소재지도로명주소']
                normalized_df['latitude'] = df['위도']
                normalized_df['longitude'] = df['경도']
                normalized_df['category_large'] = df['카테고리_대']
                normalized_df['category_small'] = df['카테고리_소']
                
            elif 'sosang' in file_name:
                normalized_df['name'] = df['상호명']
                normalized_df['address'] = df['주소']
                normalized_df['latitude'] = df['위도']
                normalized_df['longitude'] = df['경도']
                normalized_df['category_large'] = df['카테고리_대']
                normalized_df['category_small'] = df['카테고리_소']
                
            elif 'starbucks' in file_name:
                normalized_df['name'] = df['점포명']
                normalized_df['address'] = df['주소']
                normalized_df['latitude'] = df['위도']
                normalized_df['longitude'] = df['경도']
                normalized_df['category_large'] = df['카테고리_대']
                normalized_df['category_small'] = df['카테고리_소']
            
            else:
                continue
            
            normalized_df['source_file'] = file_name
            all_dfs.append(normalized_df)
            
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
            
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        # Final filter: ensure coordinates are within reasonable bounds for Seoul/S.Korea
        # 33~39 Lat, 124~131 Lon
        valid_coords = (combined_df['latitude'] > 33) & (combined_df['latitude'] < 40) & \
                      (combined_df['longitude'] > 124) & (combined_df['longitude'] < 132)
        
        # We still want to keep rows even if they have no address/lat/lon for now? 
        # Actually the user might want a clean file for mapping.
        combined_df = combined_df.dropna(subset=['name'])
        
        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Successfully combined {len(all_dfs)} files into {output_file}")
        print(f"Total rows: {len(combined_df)}")
    else:
        print("No data compiled.")

if __name__ == "__main__":
    combine_seoul_data()
