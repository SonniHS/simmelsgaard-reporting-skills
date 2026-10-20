/* ============================================================================
   OPTIONAL, PLATFORM-SPECIFIC: SQL Server / Azure SQL DB / MI
   ----------------------------------------------------------------------------
   NOT for Fabric Warehouse (no user indexes, PKs only NONCLUSTERED NOT ENFORCED).
   SQL database in Fabric: run the PKs, but SKIP the clustered columnstore index if
   the table must be mirrored to OneLake for Direct Lake (CCI tables are not mirrored).
   ========================================================================== */

ALTER TABLE gold.DimDate                 ADD CONSTRAINT PK_DimDate      PRIMARY KEY CLUSTERED ([Date]);
ALTER TABLE gold.DimScenario             ADD CONSTRAINT PK_DimScenario  PRIMARY KEY CLUSTERED (ScenarioKey);
ALTER TABLE gold.DimEntity               ADD CONSTRAINT PK_DimEntity    PRIMARY KEY CLUSTERED (EntityKey);
ALTER TABLE gold.DimAccount              ADD CONSTRAINT PK_DimAccount   PRIMARY KEY CLUSTERED (AccountKey);
ALTER TABLE gold.DimReportLine           ADD CONSTRAINT PK_DimReportLine PRIMARY KEY CLUSTERED (ReportLineKey);
ALTER TABLE gold.BridgeReportLineAccount ADD CONSTRAINT PK_BridgeRLA    PRIMARY KEY CLUSTERED (ReportLineKey, AccountKey);

CREATE UNIQUE NONCLUSTERED INDEX UX_DimEntity_Code   ON gold.DimEntity (EntityCode);
CREATE UNIQUE NONCLUSTERED INDEX UX_DimAccount_No    ON gold.DimAccount (AccountNo);
CREATE UNIQUE NONCLUSTERED INDEX UX_DimDate_DateKey  ON gold.DimDate (DateKey);

-- Fact: clustered columnstore = fast Import refresh scans and acceptable DirectQuery.
CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactFinance ON gold.FactFinance;

-- Declared FKs document the star and let the optimizer trust joins (WITH CHECK).
ALTER TABLE gold.FactFinance WITH CHECK ADD CONSTRAINT FK_Fact_Scenario FOREIGN KEY (ScenarioKey) REFERENCES gold.DimScenario (ScenarioKey);
ALTER TABLE gold.FactFinance WITH CHECK ADD CONSTRAINT FK_Fact_Date     FOREIGN KEY (PeriodDate)  REFERENCES gold.DimDate ([Date]);
ALTER TABLE gold.FactFinance WITH CHECK ADD CONSTRAINT FK_Fact_Account  FOREIGN KEY (AccountKey)  REFERENCES gold.DimAccount (AccountKey);
ALTER TABLE gold.FactFinance WITH CHECK ADD CONSTRAINT FK_Fact_Entity   FOREIGN KEY (EntityKey)   REFERENCES gold.DimEntity (EntityKey);

UPDATE STATISTICS gold.FactFinance;
