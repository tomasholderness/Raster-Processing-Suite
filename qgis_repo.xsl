<?xml version="1.0" encoding="ISO-8859-1"?>
<!-- DWXMLSource="plugins.xml" -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/plugins">
    <html>
    <head>
    <title>Tomas Holderness | QGIS Plugin repository</title>
  
    <style>
body {
	font-family:Verdana, Arial, Helvetica, sans-serif;
	width: 50em;
}
div.plugin {
	background-color:#FFFFFF;
	border:1px solid #2e465a;
	clear:both;
	display:block;
	padding:0 0 0.5em;
	margin:1em;
}
div.head {
	background-color: #2e465a;
	border-bottom-width:0;
	color: #FFFFFF;
	display:block;
	font-size:110%;
	font-weight:bold;
	margin:0;
	padding:0.3em 1em;
}

div.general{

}
div.image{
	border-bottom-width:1;
	display:block;
	margin:1;
	padding:0.3em 1em;
}
div.description {
	display: block;
	float:none;
	margin:0;
	text-align: left;
	padding:0.2em 0.5em 0.4em;
	color: black;
	font-size:100%;
	font-weight:normal;
}
div.download, div.author {
	font-size: 80%;
	padding: 0em 0em 0em 1em;
}

</style>
    </head>
    <body>
    
    <h1>Quantum GIS plugin repository</h1>
   
    <div class="general">
    QGIS plugin repository for Tomas Holderness.
	
    </div>
	
    <xsl:for-each select="/plugins/pyqgis_plugin">
      <div class="plugin">

      
        <div class="head">

            
            <xsl:value-of select="@name"/> : <xsl:value-of select="@version"/>
  
        </div>
        
        <div class="image">
        <xsl:variable name="link" select="image"/>
        <!--<img src="{$link}" />-->
        </div>

        <div class="description"> <xsl:value-of select="description"/> </div>
        <div class="download">Download: 
          <xsl:element name="a">
            <xsl:attribute name="href"> <xsl:value-of select="download_url"/> </xsl:attribute>
           <xsl:value-of select="download_url"/>
          </xsl:element>
        </div>

        
        <div class="author"> Author: <xsl:value-of select="author_name"/> </div>
        <div class="author"> QGIS minimum version: <xsl:value-of select="qgis_minimum_version"/> </div>

      </div>
    </xsl:for-each>
    </body>

    </html>
  </xsl:template>
</xsl:stylesheet>