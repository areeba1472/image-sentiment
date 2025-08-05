import React from 'react';
import './JsonTable.css'; // Optional: For styling

const JsonTable = ({ data, title, showColumnHeaders = true, columnHeaders = ['Attribute', 'Value'] }) => {
  if (!data) return null;

  return (
    <div style={{ marginBottom: '1rem' }}>
      {title && <h3 style={{ marginBottom: '0.5rem' }}>{title}</h3>}
      <table className="data-table">
        {showColumnHeaders && (
          <thead>
  <tr>
    <th>{columnHeaders[0]}</th>
    <th>{columnHeaders[1]}</th>
  </tr>
</thead>

        )}
        <tbody>
          {Object.entries(data).map(([key, value]) => (
            <tr key={key}>
              <td className="key-cell">{key}</td>
              <td className="value-cell">{typeof value === 'object' ? JSON.stringify(value) : value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default JsonTable;
