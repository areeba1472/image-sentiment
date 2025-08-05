import React from 'react';
import './MatrixTable.css'; // Optional: For styling

const MatrixTable = ({ matrix }) => {
  if (!matrix || !Array.isArray(matrix)) return null;

  return (
    <table className="matrix-table">
      <tbody>
        {matrix.map((row, i) => (
          <tr key={i}>
            {row.map((value, j) => (
              <td key={j}>{value}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default MatrixTable;
