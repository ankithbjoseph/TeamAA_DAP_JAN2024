# TeamAA_DAP_JAN2024
Database and Analytics Programming Team Project 

Team members
1. Ankith Babu Joseph- x23185813
2. Alphons Zacharia James- x23169702
3. Abhilash Janardhanan- x23121424

```mermaid
graph TD
    DS(Data Selection) -->|APIs| PP(Preprocessing/Transformation)
    PP -->|Python| MDB(MongoDB)
    MDB -->|Python| AJ(Aggregate & Join)
    AJ -->|Load| PS(PostgreSQL)
    PS --> DM(Data Mining/Analysis)
    DM --> V(Visualization)
    V --> K(Knowledge)
```
```mermaid
graph TD
    DS([Data Selection]) -->|Extract weather, air quality,<br>and footfall data| PP([Preprocessing &<br>Transformation])
    PP -->|Python scripts for cleaning<br>and transforming data| MDB([MongoDB])
    MDB -->|Join transformed data| AJ([Data Aggregation])
    AJ -->|Load to SQL database| PS([PostgreSQL])
    PS --> DA([Data Analysis])
    DA -->|Python for mining &<br>machine learning| VIS([Visualization])
    VIS --> KN([Knowledge Discovery])
    
    style DS fill:#f9f,stroke:#333,stroke-width:2px
    style PP fill:#bbf,stroke:#333,stroke-width:2px
    style MDB fill:#fdfd86,stroke:#333,stroke-width:2px
    style AJ fill:#bbf,stroke:#333,stroke-width:2px
    style PS fill:#80bfff,stroke:#333,stroke-width:2px
    style DA fill:#baffc9,stroke:#333,stroke-width:2px
    style VIS fill:#ffb347,stroke:#333,stroke-width:2px
    style KN fill:#ff6961,stroke:#333,stroke-width:2px
    
    %% Add descriptions for each node
    classDef defaultFont font-family:'Arial',font-size:14px;
    class DS,PP,MDB,AJ,PS,DA,VIS,KN defaultFont
```

```mermaid
graph LR
    subgraph Stage 1 - Data Selection
    DS([Data Selection]) -->|Extract from APIs| PP
    end

    subgraph Stage 2 - Preprocessing & Transformation
    PP([Preprocessing & Transformation]) --> MDB
    end
    
    subgraph Stage 3 - Data Integration
    MDB([MongoDB]) -->|Join| AJ
    end
    
    subgraph Stage 4 - Data Loading
    AJ([Aggregated Data]) -->|Load to PostgreSQL| PS
    end
    
    subgraph Stage 5 - Analysis & Knowledge Discovery
    PS([PostgreSQL]) --> DA([Data Analysis])
    DA --> VIS([Visualization])
    VIS --> KN([Knowledge Discovery])
    end
    
    style DS fill:#f9f,stroke:#333,stroke-width:2px
    style PP fill:#bbf,stroke:#333,stroke-width:2px
    style MDB fill:#fdfd86,stroke:#333,stroke-width:2px
    style AJ fill:#bbf,stroke:#333,stroke-width:2px
    style PS fill:#80bfff,stroke:#333,stroke-width:2px
    style DA fill:#baffc9,stroke:#333,stroke-width:2px
    style VIS fill:#ffb347,stroke:#333,stroke-width:2px
    style KN fill:#ff6961,stroke:#333,stroke-width:2px
    
    classDef defaultFont font-family:'Arial',font-size:14px;
    class DS,PP,MDB,AJ,PS,DA,VIS,KN defaultFont
```

```mermaid
graph TD
    DS(Data Selection) --> PP(Preprocessing)
    PP --> ET(ETL Processes)
    ET --> ST(Storage in MongoDB)
    ST --> TR(Transformations)
    TR --> LD(Load to PostgreSQL)
    LD --> DA(Data Analysis)
    DA --> VIZ(Visualization)
    VIZ --> KD(Knowledge Discovery)

    style DS fill:#f9f,stroke:#333,stroke-width:2px
    style PP fill:#bbf,stroke:#333,stroke-width:2px
    style ET fill:#fdfd86,stroke:#333,stroke-width:2px
    style ST fill:#bbf,stroke:#333,stroke-width:2px
    style TR fill:#80bfff,stroke:#333,stroke-width:2px
    style LD fill:#baffc9,stroke:#333,stroke-width:2px
    style DA fill:#ffb347,stroke:#333,stroke-width:2px
    style VIZ fill:#ff6961,stroke:#333,stroke-width:2px
    style KD fill:#77dd77,stroke:#333,stroke-width:2px
    
    classDef defaultFont font-family:'Arial',font-size:14px;
    class DS,PP,ET,ST,TR,LD,DA,VIZ,KD defaultFont
```

```
digraph G {
    node [shape=box, style=filled, color=lightblue];

    subgraph cluster_0 {
        label="Data Selection";
        APIs [label="APIs\n(Weather, Air Quality, Footfall)"];
    }

    subgraph cluster_1 {
        label="Preprocessing, Transformation & Storage";
        Preprocessing [label="Preprocessing\nPython Scripts"];
        Transformation [label="Transformation\nPython Scripts"];
        MongoDB [label="MongoDB\n(NoSQL Database)"];
        Preprocessing -> MongoDB;
        Transformation -> MongoDB;
    }

    subgraph cluster_2 {
        label="Data Mining/Analysis and Visualizations";
        Postgres [label="PostgreSQL\n(SQL Database)"];
        Analysis [label="Data Analysis\nPython Scripts"];
        Visualization [label="Data Visualization"];
        MongoDB -> Postgres;
        Postgres -> Analysis;
        Analysis -> Visualization;
    }

    subgraph cluster_3 {
        label="Knowledge";
        Knowledge [shape=ellipse, label="Insights and\nDecision Making"];
    }

    APIs -> Preprocessing;
    MongoDB -> Knowledge [style=dotted];
    Visualization -> Knowledge;
}
```