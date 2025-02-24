import React, { useState, useRef, useEffect } from "react";
import { FileText } from "lucide-react";
import { getCsrfCookie } from "../main";

export enum DocType {
  PDF = "pdf",
  ARXIV = "arxiv",
}

interface IngestRowsContainerProps {
  ingestArxivUrl: string;
  ingestPdfUrl: string;
  collectionId: string;
}

interface IngestRowData {
  id: number;
  docType: DocType;
  // For PDF rows
  pdfTitle: string;
  pdfFile: File | null;
  // For arXiv rows
  arxivId: string;
}

const selectedClasses = "bg-accent text-gray-shade_e";
const unselectedClasses = "bg-gray-shade_3 hover:bg-gray-shade_4";

interface DocTypeToggleProps {
  docType: DocType;
  setDocType: (docType: DocType) => void;
  arxivLogo: React.ReactNode;
}

const DocTypeToggle: React.FC<DocTypeToggleProps> = ({
  docType,
  setDocType,
  arxivLogo,
}) => {
  return (
    <div className="flex space-x-4">
      <button
        onClick={() => setDocType(DocType.PDF)}
        title="PDF"
        className={`flex items-center h-[40px] w-[40px] justify-center px-2 py-1 rounded-lg transition-colors ${
          docType === DocType.PDF ? selectedClasses : unselectedClasses
        }`}
      >
        <FileText size={18} />
      </button>

      <button
        onClick={() => setDocType(DocType.ARXIV)}
        title="arXiv"
        className={`flex items-center h-[40px] w-[40px] justify-center px-2 py-1 rounded-lg transition-colors ${
          docType === DocType.ARXIV ? selectedClasses : unselectedClasses
        }`}
      >
        {arxivLogo}
      </button>
    </div>
  );
};

const ARXIVLogo = (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="-12.5 0 100 100"
    className="w-[28px] h-[28px]"
  >
    <path
      d="M71.826 92.336 36.314 49.592l-8.977-10.558-4.977 4.656c-3.407 3.407-3.932 8.063-.437 11.558l44.495 42.379c1.035.942 2.36 1.384 3.733.965 1.485-.453 2.351-1.612 2.721-2.837.372-1.233-.174-2.326-1.047-3.419Z"
      fill="#b3aca5"
    />
    <g fill="#b32025">
      <path d="m36.314 49.592 9.557 11.503 5.761-5.356c3.513-3.513 3.465-8.318.04-11.743L7.971 2.072S6.3.044 4.534.001C2.768-.041 1.023.996.304 2.719-.384 4.37.11 5.528 1.619 7.689l29.307 35.565 5.388 6.338ZM27.61 60.663 10.494 81.687c-1.255 1.337-2.032 3.683-1.331 5.368.733 1.76 2.403 2.841 4.287 2.841 1.061 0 1.937-.373 3.082-1.523L36.86 69.474l-9.25-8.81Z" />
    </g>
    <path
      d="M64.663 12.878c-.491-1.208-2.5-2.651-3.581-2.791-1.217-.157-1.953.302-3.209 1.291L37.207 30.119l8.304 7.966 17.837-21.067c1.629-2.117 1.769-3.024 1.315-4.14Z"
      fill="#b3aca5"
    />
  </svg>
);

interface PDFFormProps {
  pdfTitle: string;
  pdfFile: File | null;
  onTitleChange: (value: string) => void;
  onFileChange: (file: File | null) => void;
}

const PDFForm: React.FC<PDFFormProps> = ({
    pdfTitle,
    pdfFile,
    onTitleChange,
    onFileChange,
  }) => {
    return (
      <div className="flex gap-4">
        <label
          htmlFor="file-upload"
          className="cursor-pointer flex items-center justify-center border border-gray-shade_6 p-2 rounded-lg hover:bg-gray-shade_3 transition-colors flex-grow h-[40px]"
        >
          {pdfFile ? pdfFile.name : "Select PDF File"}
        </label>
        <input
          id="file-upload"
          type="file"
          accept="application/pdf"
          onChange={(e) =>
            onFileChange(
              e.target.files && e.target.files.length ? e.target.files[0] : null
            )
          }
          className="hidden"
        />
  
        <input
          type="text"
          placeholder="Enter PDF title"
          value={pdfTitle}
          onChange={(e) => onTitleChange(e.target.value)}
          className="bg-gray-shade_3 border border-gray-shade_6 p-2 rounded-lg h-[40px] placeholder:text-gray-shade_a flex-grow"
        />
      </div>
    );
  };

interface ArxivFormProps {
  value: string;
  onValueChange: (value: string) => void;
}

const ArxivForm: React.FC<ArxivFormProps> = ({ value, onValueChange }) => {
  return (
    <input
      type="text"
      placeholder="Enter arXiv ID"
      value={value}
      onChange={(e) => onValueChange(e.target.value)}
      className="bg-gray-shade_3 border border-gray-shade_6 p-2 rounded-lg h-[40px] placeholder:text-gray-shade_a"
    />
  );
};

interface IngestRowProps {
  row: IngestRowData;
  onDocTypeChange: (id: number, newDocType: DocType) => void;
  onRowChange: (id: number, updates: Partial<IngestRowData>) => void;
}

const IngestRow: React.FC<IngestRowProps> = ({ row, onDocTypeChange, onRowChange }) => {
  return (
    <div className="pt-[1rem] flex items-start space-x-4">
      <DocTypeToggle
        docType={row.docType}
        setDocType={(newType) => onDocTypeChange(row.id, newType)}
        arxivLogo={ARXIVLogo}
      />
      <div className="flex-1">
        {row.docType === DocType.PDF ? (
          <PDFForm
            pdfTitle={row.pdfTitle}
            pdfFile={row.pdfFile}
            onTitleChange={(value) => onRowChange(row.id, { pdfTitle: value })}
            onFileChange={(file) => onRowChange(row.id, { pdfFile: file })}
          />
        ) : (
          <ArxivForm
            value={row.arxivId}
            onValueChange={(value) => onRowChange(row.id, { arxivId: value })}
          />
        )}
      </div>
      
    </div>
  );
};

const IngestRowsContainer: React.FC<IngestRowsContainerProps> = ({
  ingestArxivUrl,
  ingestPdfUrl,
  collectionId,
}) => {
  const [rows, setRows] = useState<IngestRowData[]>([
    { id: 1, docType: DocType.PDF, pdfTitle: "", pdfFile: null, arxivId: "" },
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [submissionMessage, setSubmissionMessage] = useState("");

  // Update a given row with new values
  const updateRow = (id: number, updates: Partial<IngestRowData>) => {
    setRows((prevRows) => {
      // Update the specified row
      const updatedRows = prevRows.map((row) =>
        row.id === id ? { ...row, ...updates } : row
      );
      
      // In this stack behavior, the active (new) row is always at index 0
      const activeRow = updatedRows[0];
      
      // Define what it means for a row to be complete
      const isComplete =
        activeRow.docType === DocType.PDF
          ? activeRow.pdfFile !== null && activeRow.pdfTitle.trim() !== ""
          : activeRow.docType === DocType.ARXIV
          ? activeRow.arxivId.trim() !== ""
          : false;
      
      // Only add a new row if the active row is the one being updated and it's complete
      if (id === activeRow.id && isComplete) {
        updatedRows.unshift({
          // Use a method to generate a unique id as needed
          id: activeRow.id + 1, 
          docType: DocType.PDF,
          pdfTitle: "",
          pdfFile: null,
          arxivId: "",
        });
      }
      
      return updatedRows;
    });
  };
  

  // When changing doc type, also clear the now-irrelevant fields.
  const updateRowDocType = (id: number, newDocType: DocType) => {
    setRows((prevRows) =>
      prevRows.map((row) =>
        row.id === id
          ? { ...row, docType: newDocType, pdfTitle: "", pdfFile: null, arxivId: "" }
          : row
      )
    );
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setSubmissionMessage("");
    // Only submit rows that are complete (skip the last empty row)
    const rowsToSubmit = rows.filter((row) =>
      row.docType === DocType.PDF
        ? row.pdfFile !== null && row.pdfTitle.trim() !== ""
        : row.docType === DocType.ARXIV
        ? row.arxivId.trim() !== ""
        : false
    );

    try {
      const promises = rowsToSubmit.map(async (row) => {
        const formData = new FormData();
        formData.append("collection", collectionId);
        if (row.docType === DocType.ARXIV) {
          formData.append("arxiv_id", row.arxivId);
          const response = await fetch(ingestArxivUrl, {
            method: "POST",
            body: formData,
            credentials: "include",
            headers : {
                "X-CSRFToken": getCsrfCookie()
            }
          });
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(
              `arXiv submission error for row ${row.id}: ${errorData.error}`
            );
          }
          return response.json();
        } else {
          // PDF submission: include the file and title.
          if (row.pdfFile) {
            formData.append("pdf_file", row.pdfFile);
          }
          formData.append("title", row.pdfTitle);
          const response = await fetch(ingestPdfUrl, {
            method: "POST",
            body: formData,
            credentials: "include",
            headers : {
                "X-CSRFToken": getCsrfCookie()
            }
          });
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(
              `PDF submission error for row ${row.id}: ${errorData.error}`
            );
          }
          return response.json();
        }
      });

      const results = await Promise.all(promises);
      setSubmissionMessage("Submission successful!");
      console.log("Submission results:", results);
      // Optionally, reset the rows to just an empty row.
      setRows([{ id: 1, docType: DocType.PDF, pdfTitle: "", pdfFile: null, arxivId: "" }]);
    } catch (error: any) {
      setSubmissionMessage(error.message || "An error occurred during submission.");
      console.error("Submission error:", error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <div
        id="rows-container"
        className="max-h-[200px] overflow-y-auto flex flex-col-reverse"
      >
        {rows.map((row) => (
          <IngestRow
            key={row.id}
            row={row}
            onDocTypeChange={updateRowDocType}
            onRowChange={updateRow}
          />
        ))}

        {submissionMessage && <div className="mt-2">{submissionMessage}</div>}
      </div>
      <button
        onClick={handleSubmit}
        disabled={submitting}
        className="mt-4 px-4 py-2 bg-accent rounded-[20px] text-gray-shade_e h-[40px]"
      >
        {submitting ? "Submitting..." : "Submit All"}
      </button>
    </>
  );
};

export default IngestRowsContainer;