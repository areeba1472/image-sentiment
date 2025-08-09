import React, { useState } from 'react';
import ResultSection from './ResultSection';
import './MetadataPage.css';
import JsonTable from './JsonTable';
import MatrixTable from './MatrixTable';
import { FaCheckCircle, FaTimesCircle } from 'react-icons/fa';
import { FaImage, FaSearch, FaSun, FaWaveSquare, FaCopy, FaCut, FaLayerGroup, FaFingerprint, FaCamera } from 'react-icons/fa';
import { mapKeysToLabels } from '../utils/MetadataMapper';
import HashTable from './HashTable';

const MetadataPage = ({ imageData }) => {
  const sections = [
    { name: 'Metadata', icon: <FaSearch /> },
    { name: 'ELA', icon: <FaLayerGroup /> },
    { name: 'Lighting Heatmap', icon: <FaSun /> },
    { name: 'Noise Map', icon: <FaWaveSquare /> },
    { name: 'Copy-Move', icon: <FaCopy /> },
    { name: 'Splicing', icon: <FaCut /> },
    { name: 'JPEG Structure', icon: <FaImage /> },
    { name: 'Digest Info', icon: <FaFingerprint /> },
    { name: 'JPEG Quality', icon: <FaCamera /> },
  ];

  const [active, setActive] = useState('Metadata');
  const elaBaseUrl = 'http://127.0.0.1:8000/';

  return (
    <>
    {/*<header className="title-bar">
      <img src="/camera.png" alt="Logo" className="logo" />
      <h1>Image Forensics Tool</h1>
    </header>*/}
    <div className="metadata-page">
      <aside className="sidebar">
        <h2>Results</h2>
        <ul>
          {sections.map(({ name, icon }) => (
            <li
              key={name}
              onClick={() => setActive(name)}
              className={active === name ? 'active' : ''}
            >
              <span className="icon">{icon}</span>
              {name}
            </li>
          ))}
        </ul>
      </aside>

      <main className="results-content">
        {active === 'Metadata' && (
          <ResultSection title="Metadata" >
            {console.log("Source Image Path:", imageData.source_image_path)}
            {imageData.source_image_path && (
              <div className="centered-image">
                <img src={`http://localhost:8000${imageData.source_image_path}`} alt="Uploaded" className="source-image" />
              </div>
            )}
            {imageData.image && (
              <div style={{ marginBottom: '1rem' }}>
                <h3>Image Name: <span style={{ fontWeight: 'normal' }}>{imageData.image}</span></h3>
              </div>
            )}

            <h3>EXIF Metadata - PIL</h3>
            {imageData.metadata_pil &&
              Object.keys(imageData.metadata_pil).filter((key) => key.toLowerCase() !== 'info').length > 0 ? (
              <JsonTable
                data={Object.fromEntries(
                  Object.entries(imageData.metadata_pil).filter(([key]) => key.toLowerCase() !== 'info')
                )}
                showColumnHeaders={false}
              />
            ) : (
              <p style={{ display: 'flex', alignItems: 'center' }}>
                <FaTimesCircle color="red" style={{ marginRight: '6px' }} />
                No image metadata found.
              </p>
            )}

            <h3>EXIF Metadata - ExifRead</h3>
            {imageData.metadata_exifread &&
              Object.keys(imageData.metadata_exifread).filter((key) => key.toLowerCase() !== 'info').length > 0 ? (
              <JsonTable
                data={Object.fromEntries(
                  Object.entries(imageData.metadata_exifread).filter(([key]) => key.toLowerCase() !== 'info')
                )}
                showColumnHeaders={false}
              />
            ) : (
              <p style={{ display: 'flex', alignItems: 'center' }}>
                <FaTimesCircle color="red" style={{ marginRight: '6px' }} />
                No image metadata found.
              </p>
            )}

            <h3>Brightness Histogram (first 10 values)</h3>
            {imageData.lighting_inconsistencies?.brightness_histogram ? (
              <JsonTable data={Object.fromEntries(
                imageData.lighting_inconsistencies.brightness_histogram
                  .slice(0, 10)
                  .map((val, idx) => [idx, val])
              )} columnHeaders={['Index', 'Value']} />
            ) : (
              <p>No brightness histogram available.</p>
            )}

            <h3>Hashes</h3>
            <HashTable data={imageData.hashes} />

            <h3>Lighting Inconsistencies</h3>
            <JsonTable
              data={mapKeysToLabels({
                mean_local_variance: imageData.lighting_inconsistencies.mean_local_variance.toFixed(2),
                std_local_variance: imageData.lighting_inconsistencies.std_local_variance.toFixed(2)
              })}
              showColumnHeaders={false}
            />

            <h3>Regional Noise Variation</h3>
            {Array.isArray(imageData.noise_analysis?.regional_variation) &&
              imageData.noise_analysis.regional_variation.length > 0 ? (
              <JsonTable
                data={Object.fromEntries(
                  mapKeysToLabels(imageData.noise_analysis.regional_variation).map(item => Object.entries(item)[0])
                )}
                columnHeaders={['Region', 'Value']}
              />

            ) : (
              <p>No regional noise variation data available.</p>
            )}

            <h3>Lighting Histogram (first 10 values)</h3>
            {Array.isArray(imageData.lighting_histogram) ? (
              <JsonTable data={Object.fromEntries(
                imageData.lighting_histogram.slice(0, 10).map((val, idx) => [idx, val])
              )} columnHeaders={['Index', 'Value']} />
            ) : (
              <p>No lighting histogram available.</p>
            )}



          </ResultSection>
        )}

        {active === 'ELA' && (
          <ResultSection title="Error Level Analysis (ELA)">
            {imageData.source_image_path && (
              <div className="centered-image">
                <img src={`http://localhost:8000${imageData.source_image_path}`} alt="Uploaded" className="source-image" />
              </div>
            )}
            <div className="centered-image">
              <img src={elaBaseUrl + imageData.ela_image_path} alt="ELA" />
            </div>

          </ResultSection>
        )}

        {active === 'Lighting Heatmap' && imageData.lighting_inconsistencies.heatmap_path && (
          <ResultSection title="Lighting Heatmap">
            {imageData.source_image_path && (
              <div className="centered-image">
                <img src={`http://localhost:8000${imageData.source_image_path}`} alt="Uploaded" className="source-image" />
              </div>
            )}
            <div className="centered-image">
              <img src={elaBaseUrl + imageData.lighting_inconsistencies.heatmap_path} alt="Heatmap" />
            </div>
          </ResultSection>
        )}

        {active === 'Noise Map' && imageData.noise_analysis.noise_map_path && (
          <ResultSection title="Noise Map">
            {imageData.source_image_path && (
              <div className="centered-image">
                <img src={`http://localhost:8000${imageData.source_image_path}`} alt="Uploaded" className="source-image" />
              </div>
            )}
            <div className="centered-image">
              <img src={elaBaseUrl + imageData.noise_analysis.noise_map_path} alt="Noise Map" />
            </div>
          </ResultSection>
        )}

        {active === 'Copy-Move' && imageData.copy_move_forgery.map_path && (
          <ResultSection title="Copy-Move Forgery">
            {imageData.source_image_path && (
              <div className="centered-image">
                <img src={`http://localhost:8000${imageData.source_image_path}`} alt="Uploaded" className="source-image" />
              </div>
            )}
            <div className="centered-image">
              <img src={elaBaseUrl + imageData.copy_move_forgery.map_path} alt="Copy Move Detection" />
            </div>
          </ResultSection>
        )}

        {active === 'Splicing' && imageData.splicing_analysis.ela_splicing_image && (
          <ResultSection title="Splicing Detection">
            {imageData.source_image_path && (
              <div className="centered-image">
                <img src={`http://localhost:8000${imageData.source_image_path}`} alt="Uploaded" className="source-image" />
              </div>
            )}
            <div className="centered-image">
              <img src={elaBaseUrl + imageData.splicing_analysis.ela_splicing_image} alt="Splicing" />
            </div>
          </ResultSection>
        )}

        {active === 'JPEG Structure' && (
          <ResultSection title="JPEG Structure Metadata">
            {imageData.source_image_path && (
              <div className="centered-image">
                <img src={`http://localhost:8000${imageData.source_image_path}`} alt="Uploaded" className="source-image" />
              </div>
            )}
            <JsonTable data={imageData.jpeg_structure_metadata} />
          </ResultSection>
        )}


        {active === 'Digest Info' && (
          <ResultSection title="Digest Information">
            {imageData.source_image_path && (
              <div className="centered-image">
                <img src={`http://localhost:8000${imageData.source_image_path}`} alt="Uploaded" className="source-image" />
              </div>
            )}
            <JsonTable
              data={imageData.digest_info}
              columnHeaders={['Attribute', 'Value']}
            />
          </ResultSection>
        )}


        {active === 'JPEG Quality' && (
          <ResultSection title="JPEG Quality Details">
            {imageData.source_image_path && (
              <div className="centered-image">
                <img src={`http://localhost:8000${imageData.source_image_path}`} alt="Uploaded" className="source-image" />
              </div>
            )}

            <h3>JPEG Quality Estimate</h3>
            <p style={{ display: 'flex', alignItems: 'center' }}>
              {imageData?.jpeg_quality_details?.quality_estimate !== undefined &&
                imageData?.jpeg_quality_details?.quality_estimate !== null ? (
                <>
                  <FaCheckCircle color="green" style={{ marginRight: '6px' }} />
                  {imageData.jpeg_quality_details.quality_estimate}
                </>
              ) : (
                <>
                  <FaTimesCircle color="red" style={{ marginRight: '6px' }} />
                  <span>This image is not in JPEG format.</span>
                </>
              )}
            </p>

            <h3>Luminance Quantization Table</h3>
            <MatrixTable matrix={imageData.jpeg_quality_details?.quantization_tables?.Luminance} />

            <h3>Chrominance Quantization Table</h3>
            <MatrixTable matrix={imageData.jpeg_quality_details?.quantization_tables?.["Chrominance 1"]} />
          </ResultSection>
        )}

      </main>
    </div>
    </>
  );
};

export default MetadataPage;
