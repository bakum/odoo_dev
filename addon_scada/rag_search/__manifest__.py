{
    'name': 'RAG Semantic Search',
    'version': '17.0.0.1',
    'depends': ['base', 'web'],
    'category': 'Tools',
    'summary': 'Semantic search across documents using FAISS (RAG without generation)',
    'application': True,
    'data': [
        'security/ir.model.access.csv',
        'views/rag_document_views.xml',
        'views/rag_chunk_views.xml',
        'data/rag_menus.xml',
        'data/search_widget.xml',
        'views/rag_config_settings.xml'
    ],
    'assets': {
        'web.assets_backend': [
            # 'rag_search/static/src/js/PDFViewer/utils/pdf_loader.js'
            'rag_search/static/src/js/chat/components/**/*.js',
            'rag_search/static/src/js/chat/components/**/*.xml',
            'rag_search/static/src/js/hooks/**/*.js',
            'rag_search/static/src/js/WordViewer/WordViewer.js',
            'rag_search/static/src/js/WordViewer/WordViewer.xml',
            'rag_search/static/src/js/PDFViewer/PDFViewer.js',
            'rag_search/static/src/js/PDFViewer/PDFViewer.xml',
            'rag_search/static/src/js/search/SemanticSearch.js',
            'rag_search/static/src/js/search/search.xml',
            'rag_search/static/src/js/chat/ChatInterface.js',
            'rag_search/static/src/js/chat/ChatInterface.xml',
            'rag_search/static/src/js/chat/ChatInterface.css'
        ]
    },
    "external_dependencies": {
        "python":
          [
           "PyMuPDF",
           "python-docx",
           "faiss-cpu",
           "numpy",
           "sentence_transformers",
           "langdetect",
           ]
    },
}