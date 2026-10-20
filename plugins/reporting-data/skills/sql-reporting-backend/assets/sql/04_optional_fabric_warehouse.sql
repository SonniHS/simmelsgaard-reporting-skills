/* ============================================================================
   OPTIONAL, PLATFORM-SPECIFIC: Fabric Warehouse
   ----------------------------------------------------------------------------
   Fabric Warehouse accepts only NONCLUSTERED ... NOT ENFORCED keys. They are not
   checked, but they document the star and are read by tools (and by Power BI when it
   suggests relationships). Uniqueness is YOUR job: run 05_checks.sql after each load,
   because a duplicate key on a one-side column makes Direct Lake queries fail.
   No indexes, no partitions in Fabric Warehouse; storage is V-Ordered Delta.
   ========================================================================== */

ALTER TABLE gold.DimDate       ADD CONSTRAINT PK_DimDate       PRIMARY KEY NONCLUSTERED ([Date])       NOT ENFORCED;
ALTER TABLE gold.DimScenario   ADD CONSTRAINT PK_DimScenario   PRIMARY KEY NONCLUSTERED (ScenarioKey)  NOT ENFORCED;
ALTER TABLE gold.DimEntity     ADD CONSTRAINT PK_DimEntity     PRIMARY KEY NONCLUSTERED (EntityKey)    NOT ENFORCED;
ALTER TABLE gold.DimAccount    ADD CONSTRAINT PK_DimAccount    PRIMARY KEY NONCLUSTERED (AccountKey)   NOT ENFORCED;
ALTER TABLE gold.DimReportLine ADD CONSTRAINT PK_DimReportLine PRIMARY KEY NONCLUSTERED (ReportLineKey) NOT ENFORCED;

ALTER TABLE gold.FactFinance ADD CONSTRAINT FK_Fact_Scenario FOREIGN KEY (ScenarioKey) REFERENCES gold.DimScenario (ScenarioKey) NOT ENFORCED;
ALTER TABLE gold.FactFinance ADD CONSTRAINT FK_Fact_Date     FOREIGN KEY (PeriodDate)  REFERENCES gold.DimDate ([Date])         NOT ENFORCED;
ALTER TABLE gold.FactFinance ADD CONSTRAINT FK_Fact_Account  FOREIGN KEY (AccountKey)  REFERENCES gold.DimAccount (AccountKey)   NOT ENFORCED;
ALTER TABLE gold.FactFinance ADD CONSTRAINT FK_Fact_Entity   FOREIGN KEY (EntityKey)   REFERENCES gold.DimEntity (EntityKey)     NOT ENFORCED;

-- Single-column statistics are allowed (multi-column manual stats are not).
CREATE STATISTICS ST_Fact_PeriodDate ON gold.FactFinance (PeriodDate);
